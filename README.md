# CapIntel-Q — Polygon Edition

## Запуск
1. `pip install -r requirements.txt`
2. Установить ключ Polygon:
   - mac/linux: `export POLYGON_API_KEY=pk_xxx`
   - Windows: `set POLYGON_API_KEY=pk_xxx`
3. `streamlit run app.py`

## Что делает
- Тянет дневные свечи из Polygon.
- Считает пивоты Фибо от прошлого периода:
  - Трейд → от прошлой **недели**
  - Среднесрок → от прошлого **месяца**
  - Долгосрок → от прошлого **года**
- «Интуитивная» логика: длинные серии Heikin-Ashi у верхних/нижних поясов → шорт/лонг; иначе — WAIT.
- Отдаёт только **цены** (вход, цели, защита), не раскрывая метод.

## Бэктест
- До 5 лет (дневки), базовый план, TP1/SL/TIMEOUT.
