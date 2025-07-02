import os
import requests
import datetime
import logging
import feedparser

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Настройки ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE = "Europe/Warsaw"

# Логирование
logging.basicConfig(level=logging.INFO)

# --- Получение данных ---
def get_usd_pln():
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=PLN")
        return round(r.json()["rates"]["PLN"], 4)
    except:
        return "н/д"

def get_brent():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1h")
        prices = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        last = next(x for x in reversed(prices) if x)
        return round(last, 2)
    except:
        return "н/д"

def get_headlines():
    feed = feedparser.parse("https://www.aljazeera.com/xml/rss/all.xml")
    keywords = ["Iran", "Israel", "missile", "Hezbollah", "attack", "strike", "Hormuz", "explosion", "military"]
    alerts = []
    for entry in feed.entries[:10]:
        if any(word.lower() in entry.title.lower() for word in keywords):
            alerts.append(f"• {entry.title}")
    return alerts

def generate_briefing():
    usd_pln = get_usd_pln()
    brent = get_brent()
    alerts = get_headlines()

    text = (
        f"📡 *Геополитическая сводка — {datetime.date.today()}*\n\n"
        f"💱 *Финансовые данные*\n"
        f"- USD/PLN: *{usd_pln}* PLN\n"
        f"- Brent: *{brent}* USD\n\n"
        f"🌍 *Новости Ближнего Востока*\n"
    )

    if alerts:
        text += "\n🚨 *Экстренные события:*\n" + "\n".join(alerts)
    else:
        text += "• Нет критических событий на текущий момент."

    text += "\n\n_Обновлено автоматически ботом_"
    return text

# --- Асинхронные обработчики ---
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

# --- Запуск ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Команда вручную
    app.add_handler(CommandHandler("update", update_command))

    # Планировщик
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(send_briefing, CronTrigger(hour=9, minute=0))         # раз в день
    scheduler.add_job(emergency_check, CronTrigger(minute="*/30"))          # каждые 30 мин
    scheduler.start()

    print("✅ Бот запущен.")
    await app.run_polling()

# Запуск
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
