# polygon_data.py
import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

POLYGON_BASE = "https://api.polygon.io/v2"

class PolygonError(RuntimeError):
    pass

def _api_key():
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        raise PolygonError("Не найден POLYGON_API_KEY. Задайте переменную окружения или добавьте её в Streamlit Secrets.")
    return key

def fetch_daily_ohlc(ticker: str, lookback_days: int = 1500) -> pd.DataFrame:
    """
    Загружает дневные свечи за lookback_days (примерно до ~6 лет).
    Возвращает DataFrame c колонками: date, open, high, low, close, volume.
    """
    key = _api_key()
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=lookback_days)
    url = f"{POLYGON_BASE}/aggs/ticker/{ticker.upper()}/range/1/day/{start}/{end}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": key}
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        raise PolygonError(f"Polygon HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not data or "results" not in data:
        raise PolygonError("Polygon вернул пустой ответ или без поля 'results'.")
    rows = data["results"]
    if not rows:
        raise PolygonError("Пустые 'results' от Polygon.")
    df = pd.DataFrame([{
        "date": pd.to_datetime(x["t"], unit="ms", utc=True).tz_convert("UTC").normalize(),
        "open": x["o"],
        "high": x["h"],
        "low": x["l"],
        "close": x["c"],
        "volume": x.get("v", None)
    } for x in rows])
    df = df.sort_values("date").reset_index(drop=True)
    return df
