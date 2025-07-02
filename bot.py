
import os
import time
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_message():
    message = (
        "📡 *Геополитическая сводка — 2 июля 2025*\n\n"
        "🌍 *Ближний Восток*\n"
        "- 🇮🇷 *Иран*: арестовано >700 человек, 6 смертных приговоров. Активизация кибератак.\n"
        "- 🇱🇧 *Ливан*: обсуждается разоружение Хезболлы. США/Катар участвуют в переговорах.\n"
        "- 🇾🇪 *Йемен*: перехват ракеты Хуситов. Возможен ответ Израиля.\n"
        "- 🌊 *Пролив Ормуз*: Иран готовит мины, но пока без блокады.\n\n"
        "💱 *Рынки*\n"
        "- USD/PLN: *3,59–3,61* PLN\n"
        "- Нефть (Brent): *$69,40*\n"
        "- DXY: в падении, худший старт с 1973 г.\n\n"
        "🔮 *Прогноз*\n"
        "- USD/PLN останется в диапазоне *3,58–3,63*\n"
        "- Следим за Ормузом, Ливаном, Ираном и курсом нефти.\n\n"
        "_Автоматическая сводка от geo_pulse_bot_"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

if __name__ == "__main__":
    send_message()
    while True:
        time.sleep(60 * 60 * 24 * 7)  # 1 раз в неделю
        send_message()
