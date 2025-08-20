import numpy as np, pandas as pd
from polygon_data import heikin_ashi, atr, prev_period_ohlc, fib_pivots

def _last_monochrome_run(ha: pd.DataFrame) -> tuple[int, str]:
    """Сколько подряд шли «зелёные» HA (HA_Close>HA_Open) или «красные»."""
    up = (ha["HA_Close"] > ha["HA_Open"]).astype(int)
    down = (ha["HA_Close"] < ha["HA_Open"]).astype(int)
    run, color = 1, "flat"
    if len(up) < 2:
        return 0, color
    # идём с конца
    i = len(up) - 1
    if up.iloc[i] == 1:
        color = "green"
        while i > 0 and up.iloc[i-1] == 1:
            run += 1; i -= 1
    elif down.iloc[i] == 1:
        color = "red"
        while i > 0 and down.iloc[i-1] == 1:
            run += 1; i -= 1
    else:
        run, color = 0, "flat"
    return run, color

def _near_belt(price: float, piv: dict, side: str, tol: float) -> bool:
    """side in {'top','bottom'} — близость к верхнему или нижнему поясу пивотов"""
    if side == "top":
        ref = piv["R2"]
        return price >= (ref - tol)
    if side == "bottom":
        ref = piv["S2"]
        return price <= (ref + tol)
    return False

def choose_period(horizon: str) -> str:
    # 'Трейд','Среднесрок','Долгосрок'
    h = horizon.lower()
    if "5" in h or "трей" in h:
        return "week"
    if "сред" in h:
        return "month"
    return "year"

def plan_for_user(df: pd.DataFrame, horizon: str) -> dict:
    """Возвращает текстовые уровни без упоминания индикаторов."""
    ha = heikin_ashi(df)
    df["ATR14"] = atr(df)
    price = float(df["Close"].iloc[-1])
    volat = float(df["ATR14"].iloc[-1])

    period = choose_period(horizon)
    H,L,C = prev_period_ohlc(df, period)
    piv = fib_pivots(H,L,C)

    run, color = _last_monochrome_run(ha)
    # пороги серии – зависят от горизонта
    need_run = 4 if period=="week" else (6 if period=="month" else 8)

    # толеранс – от волатильности
    tol = max(volat, 0.01)*1.2

    base, alt, note = {}, {}, ""
    # ЛОГИКА: длинная зелёная серия высоко → предпочтение шорту; длинная красная низко → лонг
    if run >= need_run and color == "green" and _near_belt(price, piv, "top", tol):
        # базовый: SHORT
        entry = round(price, 2)
        tp1  = round(max(piv["R1"], piv["P"]) - 0.6*volat, 2)
        tp2  = round(piv["P"] - 1.2*volat, 2)
        sl   = round(piv["R3"] + 1.0*volat, 2)
        base = {"action":"SHORT", "entry":entry, "tp1":tp1, "tp2":tp2, "sl":sl}
        # альтернатива: BUY от перегруза после отката в пояс «середины»
        alt  = {"action":"BUY",
                "entry": round(piv["P"] + 0.1*volat, 2),
                "tp1":   round(piv["R1"] - 0.3*volat, 2),
                "tp2":   round(piv["R2"] - 0.6*volat, 2),
                "sl":    round(piv["S1"] - 0.8*volat, 2)}
        note = "Рынок перегрет ростом; работаем от ослабления."
    elif run >= need_run and color == "red" and _near_belt(price, piv, "bottom", tol):
        # базовый: BUY
        entry = round(price, 2)
        tp1  = round(min(piv["S1"], piv["P"]) + 0.6*volat, 2)
        tp2  = round(piv["P"] + 1.2*volat, 2)
        sl   = round(piv["S3"] - 1.0*volat, 2)
        base = {"action":"BUY", "entry":entry, "tp1":tp1, "tp2":tp2, "sl":sl}
        # альтернатива: SHORT после отскока к средней зоне
        alt = {"action":"SHORT",
               "entry": round(piv["P"] - 0.1*volat, 2),
               "tp1":   round(piv["S1"] + 0.3*volat, 2),
               "tp2":   round(piv["S2"] + 0.6*volat, 2),
               "sl":    round(piv["R1"] + 0.8*volat, 2)}
        note = "Рынок выжат; берём восстановление."
    else:
        base = {"action":"WAIT"}
        # «область наблюдения» — не раскрываем уровни, только цены
        watch_low  = round(min(piv["P"], piv["S1"]) - 0.5*volat, 2)
        watch_high = round(max(piv["P"], piv["R1"]) + 0.5*volat, 2)
        alt  = {"action":"SCOUT", "watch_from":watch_low, "watch_to":watch_high}
        note = "Импульс не даёт преимущества."

    return {
        "price": round(price,2),
        "base": base,
        "alt": alt,
        "note": note
    }
