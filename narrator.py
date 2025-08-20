def speak(ticker: str, horizon: str, verdict: dict) -> str:
    p = verdict["price"]; base = verdict["base"]; alt = verdict["alt"]; note = verdict["note"]

    def plan_str(pl):
        if pl.get("action") == "WAIT":
            return "Сейчас лучше подождать — преимущество не на нашей стороне."
        if pl.get("action") == "SCOUT":
            return f"Наблюдаем. Интерес — при смещении цены к {pl['watch_from']}…{pl['watch_to']}."
        return (f"{pl['action']} → вход {pl['entry']}. "
                f"Цели {pl['tp1']} / {pl['tp2']}. Защита {pl['sl']}.")

    lines = []
    lines.append(f"{ticker.upper()} — {horizon}. Текущая цена: {p}.")
    if note: lines.append(note)

    lines.append("Базовый план: " + plan_str(base))
    if alt: lines.append("Альтернатива: " + plan_str(alt))
    lines.append("Работаем спокойно: если сценарий ломается — быстро выходим и ждём новую формацию.")
    return "\n".join(lines)
