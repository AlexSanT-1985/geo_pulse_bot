import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx

logging.basicConfig(level=logging.INFO)

# --- Токен и чат ---
TOKEN = "7918379447:AAGtVZXrnC5FJi8S3wPeXCyl_xaiFPgoVzg"
CHAT_ID = -1002246849121  # Заменить на свой Telegram chat_id

# --- Источники новостей ---
NEWS_SOURCES = {
    "oil": "https://oilprice.com/rss/main",
    "middle_east": "https://www.aljazeera.com/xml/rss/all.xml",
    "markets": "https://www.investing.com/rss/news_285.rss",
}

# --- Ключевые слова для фильтрации ---
KEYWORDS = [
    "houthi", "hezbollah", "israel", "iran", "red sea", "gaza",
    "opec", "strait of hormuz", "suez", "missile", "airstrike",
    "crude", "sanction", "gold", "silver", "platinum",
    "dollar index", "dxy", "inflation", "usd", "eur", "pln"
]

# --- Получение и фильтрация новостей ---
async def fetch_news_summary():
    import feedparser
    summary = []

    for name, url in NEWS_SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title.lower()
            if any(keyword in title for keyword in KEYWORDS):
                summary.append(f"• {entry.title.strip()}")

    if not summary:
        return "Нет актуальных новостей по ключевым темам."
    return "\n".join(summary[:20])

# --- Отправка сводки ---
async def send_briefing(context: ContextTypes.DEFAULT_TYPE):
    logging.info("⏰ Отправка сводки")
    try:
        summary = await fetch_news_summary()
        today = datetime.now().strftime("%d.%m.%Y")
        message = f"📊 Ежедневная сводка ({today}):\n\n{summary}"
        await context.bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сводки: {e}")

# --- Команды Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-сводки. Присылаю новости по нефти, валютам и геополитике.")

async def briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = await fetch_news_summary()
    today = datetime.now().strftime("%d.%m.%Y")
    await update.message.reply_text(f"📊 Ежедневная сводка ({today}):\n\n{summary}")

# --- Основной запуск ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("briefing", briefing))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_briefing, CronTrigger(hour=9, minute=0), kwargs={"context": type("obj", (object,), {"bot": app.bot})()})
    scheduler.start()

    logging.info("✅ Бот запущен и слушает обновления")
    await app.run_polling()

async def chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID: {update.effective_chat.id}")

app.add_handler(CommandHandler("id", chat_id))


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
