import os, streamlit as st, pandas as pd
from polygon_data import get_daily_ohlc
from core_strategy import plan_for_user
from narrator import speak
from backtest import run_backtest

st.set_page_config(page_title="CapIntel-Q • Polygon", page_icon="🧭", layout="centered")

st.title("CapIntel-Q — Polygon Edition")

with st.sidebar:
    st.subheader("Диагностика")
    st.write(f"Polygon ключ: {'ОК' if os.getenv('POLYGON_API_KEY') else 'нет'}")
    st.write("Python: ОК")
    st.caption("Источник данных: Polygon.io (аггрегированные дневные свечи)")

ticker = st.text_input("Введите тикер (например, QQQ, AAPL, X:BTCUSD):", "QQQ")
horizon = st.selectbox("Горизонт:", ["Трейд (1–5 дней)", "Среднесрок (1–4 недели)", "Долгосрок (1–6 месяцев)"])

col1, col2 = st.columns(2)
with col1:
    if st.button("Проанализировать", use_container_width=True):
        try:
            df = get_daily_ohlc(ticker, years=5)
            v = plan_for_user(df, horizon)
            st.subheader("Результат")
            st.write(speak(ticker, horizon, v))
        except Exception as e:
            st.error(f"Ошибка: {e}")

with col2:
    if st.button("Запустить бэктест", use_container_width=True):
        try:
            table, win = run_backtest(ticker, years=5, horizon=horizon)
            st.subheader("Результаты бэктеста")
            if isinstance(table, pd.DataFrame) and len(table)>0:
                st.dataframe(table, use_container_width=True, height=380)
                st.success(f"Процент срабатывания TP (по TP1): {win*100:.1f}%")
            else:
                st.info("Сигналов по базовому плану не было.")
        except Exception as e:
            st.error(f"Ошибка бэктеста: {e}")
