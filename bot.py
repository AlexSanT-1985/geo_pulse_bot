import os
import requests
import datetime
import logging
import feedparser
import asyncio

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from tzlocal import get_localzone

# === Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE = str(get_localzone()) or "Europe/Warsaw"

# === Логирование ===
logging.basicConfig(level=logging.INFO)

# === Получить курс USD/PLN ===
def get_usd_pln():
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=PLN")
        return round(r.json()["rates"]["PLN"], 4)
    except:
        return "н/д"

# === Получить цену нефти Brent ===
def get_brent():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1h")
        prices = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        last = next(x for x in reversed(prices) if x)
        return round(last, 2)
    except:
        return "н/д"

# === Получить цену золота (XAU/USD) ===
def get_gold():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=1d&interval=1h")
        prices = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        last = next(x for x in reversed(prices) if x)
        return round(last, 2)
    except:
        return "н/д"

# === Получить цену серебра (XAG/USD) ===
def get_silver():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/SI=F?range=1d&interval=1h")
        prices = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        last = next(x for x in reversed(prices) if x)
        return round(last, 2)
    except:
        return "н/д"

# === Получить заголовки с ключевыми словами ===
def get_headlines():
    feed = feedparser.parse("https://www.aljazeera.com/xml/rss/all.xml")
    keywords = ["Iran", "Israel", "missile", "Hezbollah", "attack", "strike", "Hormuz", "explosion", "military"]
    alerts = []
    for entry in feed.entries[:10]:
        if any(word.lower() in entry.title.lower() for word in keywords):
            alerts.append(f"• {entry.title}")
    return alerts

# === Сформировать текст сводки ===
def generate_briefing():
    usd_pln = get_usd_pln()
    brent = get_brent()
    gold = get_gold()
    silver = get_silver()
    alerts = get_headlines()

    text = (
        f"📡 *Геополитическая сводка — {datetime.date.today()}*\n\n"
        f"💱 *Финансовые данные*\n"
        f"- USD/PLN: *{usd_pln}* PLN\n"
        f"- Brent: *{brent}* USD\n"
        f"- Gold (XAU/USD): *{gold}* USD\n"
        f"- Silver (XAG/USD): *{silver}* USD\n\n"
        f"🌍 *Новости Ближнего Востока*\n"
    )

    if alerts:
        text += "\n🚨 *Экстренные события:*\n" + "\n".join(alerts)
    else:
        text += "• Нет критических событий на текущий момент."

    text += "\n\n_Обновлено автоматически ботом_"
    return text

# === Асинхронные действия ===
async def send_briefing(bot: Bot):
    text = generate_briefing()
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

async def emergency_check(bot: Bot):
    alerts = get_headlines()
    if alerts:
        text = "🚨 *Экстренная сводка!*\n\n" + "\n".join(alerts)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = generate_briefing()
    await update.message.reply_text(text=text, parse_mode="Markdown")

# === Главный запуск ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Планировщик задач
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(lambda: asyncio.create_task(send_briefing(app.bot)), CronTrigger(hour=9, minute=0))
    scheduler.add_job(lambda: asyncio.create_task(emergency_check(app.bot)), CronTrigger(minute="*/30"))
    scheduler.start()

    app.add_handler(CommandHandler("update", update_command))

    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.run_polling()

# === Запуск ===
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
