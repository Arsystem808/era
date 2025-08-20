# app.py
import os, streamlit as st
from polygon_data import fetch_daily_ohlc, PolygonError
from core_strategy import decide
from narrator import narrate
from backtest import run_backtest

st.set_page_config(page_title="CapIntel‑Q • Polygon", page_icon="🧭", layout="wide")

st.title("CapIntel‑Q — Polygon Edition")

ticker = st.text_input("Введите тикер (например, QQQ, AAPL, X:BTCUSD):", value="QQQ").strip().upper()
horizon = st.selectbox("Горизонт:", ["Трейд (1–5 дней)", "Среднесрок (1–4 недели)", "Долгосрок (1–6 месяцев)"])

col1, col2 = st.columns([1,1])
with col1:
    if st.button("Проанализировать", type="primary"):
        try:
            df = fetch_daily_ohlc(ticker, 1800)
            price = float(df["close"].iloc[-1])
            idea = decide(df, horizon)
            st.subheader("🧠 Результат")
            st.write(narrate(ticker, horizon, price, idea))
        except PolygonError as e:
            st.error(f"Ошибка загрузки данных: {e}")
        except Exception as e:
            st.error(f"Неожиданная ошибка: {e}")

with col2:
    if st.button("Запустить бэктест"):
        try:
            bt = run_backtest(ticker, horizon, years=5)
            if bt.empty:
                st.warning("Бэктест не нашёл сделок по текущим фильтрам.")
            else:
                st.dataframe(bt)
                win = (bt["ret_pct"]>0).mean()*100
                st.success(f"Всего сделок: {len(bt)}, доля положительных: {win:.1f}%")
        except PolygonError as e:
            st.error(f"Ошибка загрузки данных: {e}")
        except Exception as e:
            st.error(f"Неожиданная ошибка: {e}")

st.divider()
with st.expander("Диагностика"):
    st.write(f"POLYGON_API_KEY установлен: {'Да' if os.environ.get('POLYGON_API_KEY') else 'Нет'}")
    st.write("Приложение не раскрывает внутренние расчёты и говорит «по‑человечески».")
