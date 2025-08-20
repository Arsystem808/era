# narrator.py
def narrate(ticker: str, horizon_label: str, price: float, idea: dict) -> str:
    act = idea["action"]
    entry = idea["entry"]
    tp1, tp2, sl = idea["tp1"], idea["tp2"], idea["sl"]
    notes = idea.get("notes", [])
    lines = []
    lines.append(f"{ticker} — {horizon_label}. Текущая цена: {price:.2f}.")
    if act == "WAIT":
        lines.append("Сейчас поспешность не даст преимущества. Дождёмся понятной формации.")
        if isinstance(entry, str):
            lines.append(f"Область внимания: {entry}.")
    elif act == "BUY":
        lines.append("Покупка смотрится оправданно — перевес на нашей стороне.")
        lines.append(f"Вход: {entry}.")
        if tp1: lines.append(f"Цели: {tp1}" + (f" / {tp2}" if tp2 else "" ) + ".")
        if sl:  lines.append(f"Защита: {sl}.")
    elif act == "SHORT":
        lines.append("Игра от шорта выглядит здраво — рынок переутомился у верхней кромки.")
        lines.append(f"Вход: {entry}.")
        if tp1: lines.append(f"Цели: {tp1}" + (f" / {tp2}" if tp2 else "" ) + ".")
        if sl:  lines.append(f"Защита: {sl}.")
    for n in notes:
        lines.append(n)
    return "\n".join(lines)
