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
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Или вставь как строку: TOKEN = "your_token"
CHAT_ID = os.getenv("CHAT_ID")       # Или напрямую: CHAT_ID = "123456789"
TIMEZONE = "Europe/Warsaw"

# Логирование
logging.basicConfig(level=logging.INFO)

# --- Получить курс USD/PLN ---
def get_usd_pln():
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=PLN")
        return round(r.json()["rates"]["PLN"], 4)
    except Exception as e:
        logging.error(f"Ошибка при получении курса USD/PLN: {e}")
        return "н/д"

# --- Получить цену нефти Brent ---
def get_brent():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1h")
        prices = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        last = next(x for x in reversed(prices) if x)
        return round(last, 2)
    except Exception as e:
        logging.error(f"Ошибка при получении Brent: {e}")
        return "н/д"

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

# --- Отправить плановую сводку ---
async def send_briefing(context: ContextTypes.DEFAULT_TYPE):
    text = generate_briefing()
    await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

# --- Команда /update ---
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = generate_briefing()
    await update.message.reply_text(text=text, parse_mode="Markdown")

# --- Проверка экстренных новостей ---
async def emergency_check(context: ContextTypes.DEFAULT_TYPE):
    alerts = get_headlines()
    if alerts:
        text = "🚨 *Экстренная сводка!*\n\n" + "\n".join(alerts)
        await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

# --- Запуск приложения ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Команда /update вручную
    app.add_handler(CommandHandler("update", update_command))

    # Планировщик задач
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(send_briefing, CronTrigger(hour=9, minute=0))        # Автоотчёт в 9:00
    scheduler.add_job(emergency_check, CronTrigger(minute="*/30"))        # Экстренные события каждые 30 мин
    scheduler.start()

    app.run_polling()
