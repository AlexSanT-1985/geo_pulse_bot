import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import feedparser
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import nest_asyncio
import os

nest_asyncio.apply()

TOKEN = os.getenv("BOT_TOKEN")  # Или замени на строку токена вручную
CHAT_ID = os.getenv("CHAT_ID")  # Или замени вручную, если знаешь chat_id
TIMEZONE = "Europe/Warsaw"

RSS_FEEDS = [
    "https://www.reutersagency.com/feed/?best-topics=top-news",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.marketwatch.com/rss/topstories"
]

async def fetch_news():
    news = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:  # первые 3 статьи
            news.append(f"📰 <b>{entry.title}</b>\n{entry.link}")
    return "\n\n".join(news[:9])  # максимум 9 новостей

async def fetch_metals():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.metals.live/v1/spot")
            data = res.json()[0]
            return (
                "📈 <b>Металлы (USD/oz):</b>\n"
                f"• Золото: {data.get('gold', '—')}\n"
                f"• Серебро: {data.get('silver', '—')}\n"
                f"• Платина: {data.get('platinum', '—')}\n"
                f"• Палладий: {data.get('palladium', '—')}"
            )
    except Exception as e:
        return f"⚠️ Не удалось загрузить данные по металлам: {e}"

async def send_briefing(bot: Bot):
    news = await fetch_news()
    metals = await fetch_metals()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"<b>🗓 Утренняя сводка — {now}</b>\n\n{metals}\n\n{news}"
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")

async def emergency_check(bot: Bot):
    await bot.send_message(chat_id=CHAT_ID, text="✅ Бот работает (проверка 30 мин)", parse_mode="HTML")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Обновляю...", parse_mode="HTML")
    await send_briefing(context.bot)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Удаляем старые getUpdates-сессии
    await app.bot.delete_webhook(drop_pending_updates=True)

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(lambda: asyncio.create_task(send_briefing(app.bot)), CronTrigger(hour=9, minute=0))
    scheduler.add_job(lambda: asyncio.create_task(emergency_check(app.bot)), CronTrigger(minute="*/30"))
    scheduler.start()

    app.add_handler(CommandHandler("update", update_command))
    print("✅ Bot is running...")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
