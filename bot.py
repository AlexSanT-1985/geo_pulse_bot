import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx

logging.basicConfig(level=logging.INFO)

TOKEN = "your_bot_token_here"

# --- Источники новостей ---
NEWS_SOURCES = {
    "oil": "https://oilprice.com/rss/main",
    "middle_east": "https://www.aljazeera.com/xml/rss/all.xml",
    "markets": "https://www.investing.com/rss/news_285.rss",
}

# --- Ключевые слова ---
KEYWORDS = [
    "houthi", "hezbollah", "israel", "iran", "red sea", "gaza",
    "opec", "strait of hormuz", "suez", "missile", "airstrike",
    "crude", "sanction", "gold", "dollar index", "dxy",
    "inflation", "pln", "eur", "usd"
]

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

async def send_briefing(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
    logging.info("⏰ Отправка аналитической сводки")
    try:
        summary = await fetch_news_summary()
        today = datetime.now().strftime("%d.%m.%Y")
        message = f"📊 Ежедневная сводка ({today}):\n\n{summary}"
        await context.bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сводки: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-аналитик. Каждый день в 9:00 по UTC присылаю сводку по нефти, Ближнему Востоку и валютам.")
    logging.info(f"Пользователь стартовал: {update.effective_chat.id}")

async def briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = await fetch_news_summary()
    today = datetime.now().strftime("%d.%m.%Y")
    await update.message.reply_text(f"📊 Ежедневная сводка ({today}):\n\n{summary}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("briefing", briefing))

    # Получаем ID чата при первом использовании /start
    async def schedule_job(application):
        await asyncio.sleep(2)  # даем боту стартовать
        # вручную вставь chat_id после получения через /start или /briefing
        chat_id = your_chat_id_here  # ← ЗАМЕНИ НА ЧИСЛО
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            send_briefing,
            CronTrigger(hour=9, minute=0),
            kwargs={"context": {"chat_id": chat_id}},
        )
        scheduler.start()

    asyncio.create_task(schedule_job(app))
    logging.info("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
