import os
import requests
import datetime
import logging
import feedparser
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Константы ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE = "Europe/Warsaw"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# --- Получить курс USD/PLN ---
def get_usd_pln():
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=PLN", timeout=10)
        return round(r.json()["rates"]["PLN"], 4)
    except Exception as e:
        logging.error(f"USD/PLN error: {e}")
        return "н/д"

# --- Получить цену нефти Brent ---
def get_brent():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1h", headers=HEADERS, timeout=10)
        prices = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        last = next(x for x in reversed(prices) if x is not None)
        return round(last, 2)
    except Exception as e:
        logging.error(f"Brent error: {e}")
        return "н/д"

# --- Получить цены на металлы ---
def get_metals():
    prices = {}
    symbols = {
        "gold": "GC=F",
        "silver": "SI=F",
        "platinum": "PL=F"
    }
    for name, symbol in symbols.items():
        try:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1h", headers=HEADERS, timeout=10)
            data = r.json()
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            last_price = next(x for x in reversed(closes) if x is not None)
            prices[name] = round(last_price, 2)
        except Exception as e:
            logging.error(f"[{name.upper()}] metals error: {e}")
            prices[name] = "н/д"
    return prices

# --- Получить экстренные заголовки ---
def get_headlines():
    feed = feedparser.parse("https://www.aljazeera.com/xml/rss/all.xml")
    keywords = ["Iran", "Israel", "missile", "Hezbollah", "attack", "strike", "Hormuz", "explosion", "military"]
    alerts = []
    for entry in feed.entries[:10]:
        if any(word.lower() in entry.title.lower() for word in keywords):
            alerts.append(f"• {entry.title}")
    return alerts

# --- Сформировать текст сводки ---
def generate_briefing():
    usd_pln = get_usd_pln()
    brent = get_brent()
    metals = get_metals()
    alerts = get_headlines()

    text = (
        f"📡 *Геополитическая сводка — {datetime.date.today()}*\n\n"
        f"💱 *Финансовые данные*\n"
        f"- USD/PLN: *{usd_pln}* PLN\n"
        f"- Brent: *{brent}* USD\n\n"
        f"📈 *Драгоценные металлы* _(за унцию)_\n"
        f"- Золото: *{metals['gold']}* USD\n"
        f"- Серебро: *{metals['silver']}* USD\n"
        f"- Платина: *{metals['platinum']}* USD\n\n"
        f"🌍 *Новости Ближнего Востока*\n"
    )

    if alerts:
        text += "\n🚨 *Экстренные события:*\n" + "\n".join(alerts)
    else:
        text += "• Нет критических событий на текущий момент."

    text += "\n\n_Обновлено автоматически ботом_"
    return text

# --- Отправка сообщений ---
async def send_briefing(context: ContextTypes.DEFAULT_TYPE):
    text = generate_briefing()
    await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

async def emergency_check(context: ContextTypes.DEFAULT_TYPE):
    alerts = get_headlines()
    if alerts:
        text = "🚨 *Экстренная сводка!*\n\n" + "\n".join(alerts)
        await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = generate_briefing()
    await update.message.reply_text(text=text, parse_mode="Markdown")

# --- Главная функция ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Планировщик
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(lambda: send_briefing(app), CronTrigger(hour=9, minute=0))
    scheduler.add_job(lambda: emergency_check(app), CronTrigger(minute="*/30"))
    scheduler.start()

    # Команда /update
    app.add_handler(CommandHandler("update", update_command))

    # Запуск
    await app.run_polling()

# --- Запуск ---
if __name__ == "__main__":
    asyncio.run(main())
