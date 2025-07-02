import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import feedparser
import httpx
import nest_asyncio

logging.basicConfig(level=logging.INFO)

TOKEN = "7918379447:AAGtVZXrnC5FJi8S3wPeXCyl_xaiFPgoVzg"
CHAT_ID = 754867580  # замените на свой chat_id

# --- Аналитическая сводка: источники ---
NEWS_SOURCES = {
    "oil": "https://oilprice.com/rss/main",
    "middle_east": "https://www.aljazeera.com/xml/rss/all.xml",
    "markets": "https://www.investing.com/rss/news_285.rss",
}

KEYWORDS = [
    "houthi", "hezbollah", "israel", "iran", "red sea", "gaza", "opec",
    "strait of hormuz", "suez", "missile", "airstrike", "crude", "sanction",
    "gold", "silver", "platinum", "dollar index", "dxy", "inflation", "pln", "eur", "usd"
]

async def fetch_news_summary():
    summary = []
    for name, url in NEWS_SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title.lower()
            if any(keyword in title for keyword in KEYWORDS):
                summary.append(f"• {entry.title.strip()}")
    return "\n".join(summary[:20]) if summary else "Нет актуальных новостей по ключевым темам."

async def send_briefing(app):
    logging.info("⏰ Отправка аналитической сводки")
    try:
        summary = await fetch_news_summary()
        today = datetime.now().strftime("%d.%m.%Y")
        message = f"📊 Ежедневная сводка ({today}):\n\n{summary}"
        await app.bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сводки: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-аналитик. Каждый день в 9:00 по UTC присылаю сводку по нефти, Ближнему Востоку и валютам.\n\nНапиши /briefing чтобы получить сводку вручную.")

async def briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = await fetch_news_summary()
    today = datetime.now().strftime("%d.%m.%Y")
    await update.message.reply_text(f"📊 Ежедневная сводка ({today}):\n\n{summary}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("briefing", briefing))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(send_briefing(app)), CronTrigger(hour=9, minute=0))
    scheduler.start()

    logging.info("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
