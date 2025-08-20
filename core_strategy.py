# core_strategy.py
from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class PivotLevels:
    P: float
    R1: float
    R2: float
    R3: float
    S1: float
    S2: float
    S3: float

def heikin_base(df: pd.DataFrame) -> pd.DataFrame:
    """Внутреннее сглаживание (без разглашения наружу)."""
    ha = df.copy()
    ha["h_close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4.0
    ha["h_open"] = (df["open"].shift(1).fillna(df["open"]) + df["close"].shift(1).fillna(df["open"])) / 2.0
    ha["h_high"] = ha[["h_open", "h_close", "high"]].max(axis=1)
    ha["h_low"]  = ha[["h_open", "h_close", "low"]].min(axis=1)
    ha["h_color"] = np.where(ha["h_close"] >= ha["h_open"], 1, -1)
    return ha

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = np.maximum.reduce([high-low, (high - prev_close).abs(), (low - prev_close).abs()])
    return tr.rolling(n, min_periods=1).mean()

def last_closed_period_hlc(df: pd.DataFrame, scope: str) -> tuple[float, float, float]:
    idx = df.index
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    if scope == "short":
        # прошлая календарная неделя
        d["year"] = d["date"].dt.isocalendar().year
        d["week"] = d["date"].dt.isocalendar().week
        last_y, last_w = d.iloc[-1][["year","week"]]
        mask = (d["year"] < last_y) | ((d["year"] == last_y) & (d["week"] < last_w))
        past = d[mask]
        if past.empty:
            past = d.iloc[:-1]
        grp = past.groupby(["year","week"])[["high","low","close"]].agg({"high":"max","low":"min","close":"last"}).reset_index(drop=True)
        period = grp.iloc[-1]
    elif scope == "mid":
        # прошлый месяц
        d["ym"] = d["date"].dt.to_period("M")
        last_ym = d.iloc[-1]["ym"]
        past = d[d["ym"] < last_ym]
        if past.empty:
            past = d.iloc[:-1]
        grp = past.groupby("ym")[["high","low","close"]].agg({"high":"max","low":"min","close":"last"}).reset_index(drop=True)
        period = grp.iloc[-1]
    else:
        # прошлый год
        d["y"] = d["date"].dt.year
        last_y = d.iloc[-1]["y"]
        past = d[d["y"] < last_y]
        if past.empty:
            past = d.iloc[:-1]
        grp = past.groupby("y")[["high","low","close"]].agg({"high":"max","low":"min","close":"last"}).reset_index(drop=True)
        period = grp.iloc[-1]
    return float(period["high"]), float(period["low"]), float(period["close"])

def fib_pivots_from(prev_high: float, prev_low: float, prev_close: float) -> PivotLevels:
    P = (prev_high + prev_low + prev_close) / 3.0
    rng = prev_high - prev_low
    R1 = P + 0.382 * rng
    R2 = P + 0.618 * rng
    R3 = P + 1.000 * rng
    S1 = P - 0.382 * rng
    S2 = P - 0.618 * rng
    S3 = P - 1.000 * rng
    return PivotLevels(P, R1, R2, R3, S1, S2, S3)

def decide(df: pd.DataFrame, horizon: str) -> dict:
    # horizon: "short" (1-5д), "mid" (1-4нед), "long" (1-6мес)
    scope = {"Трейд (1–5 дней)":"short", "Среднесрок (1–4 недели)":"mid", "Долгосрок (1–6 месяцев)":"long"}.get(horizon, "mid")
    ha = heikin_base(df)
    recent = ha.iloc[-80:].copy()
    # серия цвета
    recent["run"] = (recent["h_color"] != recent["h_color"].shift(1)).cumsum()
    run_len = recent.groupby("run")["h_color"].transform("size")
    last_run_len = int(run_len.iloc[-1])
    last_color = int(recent["h_color"].iloc[-1])
    # пивоты по прошлому завершенному периоду
    ph, pl, pc = last_closed_period_hlc(df, scope)
    piv = fib_pivots_from(ph, pl, pc)
    last_close = float(df["close"].iloc[-1])
    # ATR для масштаба
    a = float(atr(df, 14).iloc[-1])
    if a <= 0 or np.isnan(a): a = max(1.0, (df["high"].iloc[-30:-1].max() - df["low"].iloc[-30:-1].min())/30.0)

    # расстояния
    top = piv.R3
    bottom = piv.S3
    center = piv.P

    # логика "интуиции"
    near_top = last_close > piv.R2
    near_bottom = last_close < piv.S2
    long_green = (last_color == 1 and last_run_len >= 5)
    long_red   = (last_color == -1 and last_run_len >= 5)

    idea = {"action":"WAIT", "entry":None, "tp1":None, "tp2":None, "sl":None, "notes":[]}

    width = max(2*a, (piv.R2 - piv.S2)/12.0)  # разумная ширина зоны/стопа

    if near_top and long_green:
        # базово: шорт сверху
        idea["action"] = "SHORT"
        idea["entry"] = round(last_close, 2)
        idea["tp1"] = round((center + piv.R1)/2.0, 2)  # к центру
        idea["tp2"] = round(center, 2)
        idea["sl"] = round(min(top + width, last_close + 2*width), 2)
        idea["notes"].append("Рынок выглядел перегретым у верхней кромки; берём там, где перевес наш.")
    elif near_bottom and long_red:
        # базово: лонг снизу
        idea["action"] = "BUY"
        idea["entry"] = round(last_close, 2)
        idea["tp1"] = round((center + piv.S1)/2.0, 2)
        idea["tp2"] = round(center, 2)
        idea["sl"] = round(max(bottom - width, last_close - 2*width), 2)
        idea["notes"].append("Рынок выглядел истощённым у нижней кромки; берём там, где перевес наш.")
    else:
        # нет явного перевеса — ждём формацию и даём зону внимания
        idea["notes"].append("Сейчас вход не даёт преимущества. Ждём формацию в области интереса.")
        # область интереса ближе к центру баланса периода
        z1 = round(center - a, 2)
        z2 = round(center + a, 2)
        idea["entry"] = f"{z1}–{z2}"
        # защиту и цели не навязываем, чтобы не провоцировать «тонкие» входы
        idea["tp1"] = None
        idea["tp2"] = None
        idea["sl"] = None

    # сглаживание экстремумов для долгосрока (чтобы не были «коротышами»)
    if scope == "long" and idea["action"] in ("BUY","SHORT"):
        # растянуть цели минимум на 1.5*ATR от entry в сторону замысла,
        # но не выходя за логичный центр периода
        if idea["action"] == "SHORT":
            min_tp = idea["entry"] - 1.5*a
            idea["tp1"] = round(min(idea["tp1"], min_tp), 2) if idea["tp1"] else round(min_tp, 2)
        else:
            min_tp = idea["entry"] + 1.5*a
            idea["tp1"] = round(max(idea["tp1"], min_tp), 2) if idea["tp1"] else round(min_tp, 2)

    # финальная заметка
    idea["notes"].append("Работаем спокойно: если сценарий ломается — быстро выходим и ждём новую формацию.")
    # упаковка
    idea["meta"] = {"pivot_center": round(center,2)}
    return idea
