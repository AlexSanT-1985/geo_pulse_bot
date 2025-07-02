import os
import requests
import datetime
import logging
import feedparser
import asyncio
import nest_asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Настройки ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE = "Europe/Warsaw"

# Включить логирование
logging.basicConfig(level=logging.INFO)

# --- Получить курс USD/PLN ---
def get_usd_pln():
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=PLN")
        return round(r.json()["rates"]["PLN"], 4)
    except:
        return "н/д"

# --- Получить цену нефти Brent ---
def get_brent():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1h")
        prices = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        last = next(x for x in reversed(prices) if x)
        return round(last, 2)
    except:
        return "н/д"

# --- Получить цену золота и серебра ---
def get_metals():
    try:
        r = requests.get("https://api.metals.live/v1/spot")
        data = r.json()
        gold = next((x['gold'] for x in data if 'gold' in x), None)
        silver = next((x['silver'] for x in data if 'silver' in x), None)
        return round(gold, 2), round(silver, 2)
    except:
        return "н/д", "н/д"

# --- Получить экстренные заголовки ---
def get_headlines():
    feed = feedparser.parse("https://www.aljazeera.com/xml/rss/all.xml")
    keywords = ["Iran", "Israel", "missile", "Hezbollah", "attack", "strike", "Hormuz", "explosion", "military"]
    alerts = []
    for entry in feed.entries[:10]:
        if any(word.lower() in entry.title.lower() for word in keywords):
            alerts.append(f"• {entry.title}")
    return alerts

# --- Сформировать сводку ---
def generate_briefing():
    usd_pln = get_usd_pln()
    brent = get_brent()
    gold, silver = get_metals()
    alerts = get_headlines()

    text = (
        f"📡 *Геополитическая сводка — {datetime.date.today()}*\n\n"
        f"💱 *Финансовые данные*\n"
        f"- USD/PLN: *{usd_pln}* PLN\n"
        f"- Brent: *{brent}* USD\n"
        f"- Gold: *{gold}* USD/oz\n"
        f"- Silver: *{silver}* USD/oz\n\n"
        f"🌍 *Новости Ближнего Востока*\n"
    )

    if alerts:
        text += "\n🚨 *Экстренные события:*\n" + "\n".join(alerts)
    else:
        text += "• Нет критических событий на текущий момент."

    text += "\n\n_Обновлено автоматически ботом_"
    return text

# --- Асинхронные действия ---
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

# --- Главный запуск ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Планировщик
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(send_briefing, CronTrigger(hour=9, minute=0))
    scheduler.add_job(emergency_check, CronTrigger(minute="*/30"))
    scheduler.start()

    # Команда /update
    app.add_handler(CommandHandler("update", update_command))

    # Запуск
    await app.run_polling()

# --- Запуск ---
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
