import pandas as pd, numpy as np, datetime as dt
from polygon_data import get_daily_ohlc
from core_strategy import plan_for_user, choose_period

def run_backtest(ticker: str, years: int = 5, horizon: str = "Долгосрок"):
    df = get_daily_ohlc(ticker, years=years)
    res = []
    # шаг по дням: генерируем сигнал и держим позицию до TP1 или SL или таймаут
    timeout = 5 if "трей" in horizon.lower() else (20 if "сред" in horizon.lower() else 60)

    for i in range(60, len(df)-1):
        window = df.iloc[:i+1].copy()
        verdict = plan_for_user(window, horizon)
        base = verdict["base"]
        if base.get("action") not in ("BUY","SHORT"):
            continue
        entry = base["entry"]; tp = base["tp1"]; sl = base["sl"]
        opened = False
        direction = 1 if base["action"]=="BUY" else -1
        open_idx = i+1
        if open_idx >= len(df): break
        # открываем по следующему дню по цене открытия
        entry_px = float(df["Open"].iloc[open_idx])
        # симуляция
        outcome, days = "TIMEOUT", 0
        for j in range(open_idx, min(open_idx+timeout, len(df))):
            hi = float(df["High"].iloc[j]); lo = float(df["Low"].iloc[j])
            if direction==1:
                if lo <= sl: outcome="SL"; days=j-open_idx+1; break
                if hi >= tp: outcome="TP"; days=j-open_idx+1; break
            else:
                if hi >= sl: outcome="SL"; days=j-open_idx+1; break
                if lo <= tp: outcome="TP"; days=j-open_idx+1; break
        res.append({
            "date": df["Date"].iloc[i].date().isoformat(),
            "signal": base["action"],
            "entry": entry_px,
            "tp": tp, "sl": sl,
            "outcome": outcome,
            "days": days
        })
    if not res:
        return pd.DataFrame()
    out = pd.DataFrame(res)
    win = (out["outcome"]=="TP").mean() if len(out)>0 else 0.0
    return out, win
