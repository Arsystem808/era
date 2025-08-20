import os, datetime as dt, pandas as pd, requests as rq

POLY_KEY = os.getenv("POLYGON_API_KEY", "")

def _poly_url(ticker, start, end):
    return (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
        f"{start}/{end}?adjusted=true&sort=asc&limit=50000&apiKey={POLY_KEY}"
    )

def get_daily_ohlc(ticker: str, years: int = 5) -> pd.DataFrame:
    if not POLY_KEY:
        raise RuntimeError("POLYGON_API_KEY не найден в окружении.")
    end = dt.date.today()
    start = end - dt.timedelta(days=365*years + 10)

    url = _poly_url(ticker.upper(), start.isoformat(), end.isoformat())
    r = rq.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()
    if js.get("resultsCount", 0) == 0 or "results" not in js:
        raise RuntimeError(f"Polygon вернул пусто для {ticker}")

    rows = js["results"]
    df = pd.DataFrame(rows)
    # поля: t (ms), o,h,l,c,v
    df["Date"] = pd.to_datetime(df["t"], unit="ms").dt.tz_localize(None)
    df = df[["Date","o","h","l","c","v"]].rename(
        columns={"o":"Open","h":"High","l":"Low","c":"Close","v":"Volume"}
    ).sort_values("Date").reset_index(drop=True)
    return df

def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    ha = df.copy()
    ha["HA_Close"] = (ha["Open"] + ha["High"] + ha["Low"] + ha["Close"]) / 4.0
    ha["HA_Open"] = 0.0
    # инициализация
    ha.loc[0, "HA_Open"] = (ha.loc[0, "Open"] + ha.loc[0, "Close"]) / 2.0
    for i in range(1, len(ha)):
        ha.loc[i, "HA_Open"] = (ha.loc[i-1, "HA_Open"] + ha.loc[i-1, "HA_Close"]) / 2.0
    ha["HA_High"] = ha[["High","HA_Open","HA_Close"]].max(axis=1)
    ha["HA_Low"]  = ha[["Low","HA_Open","HA_Close"]].min(axis=1)
    return ha

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    # True Range
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low  - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def prev_period_ohlc(df: pd.DataFrame, mode: str) -> tuple[float,float,float]:
    """ mode: 'week'|'month'|'year' — берём ПРЕДЫДУЩИЙ полностью закрытый период """
    d = df.copy().set_index("Date")
    if mode == "week":
        g = d.resample("W-FRI").agg({"Open":"first","High":"max","Low":"min","Close":"last"})
    elif mode == "month":
        g = d.resample("M").agg({"Open":"first","High":"max","Low":"min","Close":"last"})
    elif mode == "year":
        g = d.resample("Y").agg({"Open":"first","High":"max","Low":"min","Close":"last"})
    else:
        raise ValueError("bad mode")
    if len(g) < 2:
        # недостаточно истории – возьмём последний полный отрезок из 20 дней
        tail = d.iloc[:-1].tail(20)
        return tail["High"].max(), tail["Low"].min(), tail["Close"].iloc[-1]
    prev = g.iloc[-2]
    return float(prev["High"]), float(prev["Low"]), float(prev["Close"])

def fib_pivots(H, L, C):
    P = (H + L + C) / 3.0
    rng = H - L
    return {
        "P": P,
        "R1": P + 0.382*rng, "S1": P - 0.382*rng,
        "R2": P + 0.618*rng, "S2": P - 0.618*rng,
        "R3": P + 1.000*rng, "S3": P - 1.000*rng
    }
