# backtest.py
import pandas as pd
from core_strategy import decide
from polygon_data import fetch_daily_ohlc

def run_backtest(ticker: str, horizon_label: str, years: int = 5) -> pd.DataFrame:
    df = fetch_daily_ohlc(ticker, lookback_days=365*years+30)
    # дневной бэктест: каждый день пересчитываем идею, входим на следующий бар по market,
    # выходим по TP1/TP2/SL/макс дней удержания (20 для трейда, 60 среднесрок, 120 долгосрок)
    max_hold = {"Трейд (1–5 дней)":20, "Среднесрок (1–4 недели)":60, "Долгосрок (1–6 месяцев)":120}.get(horizon_label, 60)
    trades = []
    for i in range(60, len(df)-2):
        window = df.iloc[:i+1].copy()
        idea = decide(window, horizon_label)
        act = idea["action"]
        if act == "WAIT" or idea["entry"] is None or isinstance(idea["entry"], str):
            continue
        entry_price = float(idea["entry"])
        entry_idx = i+1
        side = 1 if act=="BUY" else -1
        tp1 = idea["tp1"]; tp2 = idea["tp2"]; sl = idea["sl"]
        exit_price = None; exit_idx = None; reason = None
        for j in range(entry_idx, min(entry_idx+max_hold, len(df))):
            hi = df["high"].iloc[j]; lo = df["low"].iloc[j]
            if side==1:
                if tp1 and hi>=tp1: exit_price, exit_idx, reason = tp1, j, "TP1"; break
                if sl and lo<=sl:    exit_price, exit_idx, reason = sl, j, "SL";  break
            else:
                if tp1 and lo<=tp1: exit_price, exit_idx, reason = tp1, j, "TP1"; break
                if sl and hi>=sl:   exit_price, exit_idx, reason = sl, j, "SL";  break
        if exit_price is None:
            exit_price = float(df["close"].iloc[min(entry_idx+max_hold-1, len(df)-1)])
            exit_idx = min(entry_idx+max_hold-1, len(df)-1)
            reason = "TIME"
        ret = (exit_price-entry_price)/entry_price * (1 if side==1 else -1)
        trades.append({
            "date": df["date"].iloc[entry_idx].date(),
            "side": act,
            "entry": entry_price,
            "exit": exit_price,
            "reason": reason,
            "ret_pct": round(100*ret, 2)
        })
    return pd.DataFrame(trades)
