from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, time
from logging.handlers import RotatingFileHandler

import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai_utils import generate_ai_response, get_scheduled_theme, is_unique, save_history

# Logging configuration
os.makedirs("logs", exist_ok=True)
log_format = "[%(asctime)s] %(levelname)s: %(message)s"
file_handler = RotatingFileHandler(
    "logs/bot.log", maxBytes=5 * 1024 * 1024, backupCount=3
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format))

stderr_handler = logging.StreamHandler()
stderr_handler.setLevel(logging.WARNING)
stderr_handler.setFormatter(logging.Formatter(log_format))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, stderr_handler])


# Environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

if not all([TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, TARGET_CHAT_ID]):
    logging.critical("Required environment variables are missing")
    raise SystemExit(1)

openai.api_key = OPENAI_API_KEY


async def start_command(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message."""
    now = datetime.now().strftime("%Y-%m-%d")
    await update.message.reply_text(f"Вітаю! Сьогодні {now}.")


async def echo(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo any non-command text message."""
    await update.message.reply_text(update.message.text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to user messages in Nikita's style."""
    message_text = update.message.text
    user_name = update.effective_user.first_name
    prompt = (
        f"Користувач на ім'я '{user_name}' пише в чаті: '{message_text}'. "
        "Дай відповідь в стилі Нікіти, звертаючись до користувача."
    )
    ai_response = generate_ai_response(prompt)
    await update.message.reply_text(ai_response)


async def scheduled_post_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send a daily post according to schedule."""
    theme = get_scheduled_theme()
    if not theme:
        logging.warning("Не найдена тема для сегодняшнего поста")
        return
    prompt = f"Напиши пост на тему '{theme}'."
    post = generate_ai_response(prompt)
    if is_unique(post):
        await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=post)
        save_history(post)
        logging.info("Scheduled post sent")
    else:
        logging.warning("Дубликат поста, отправка отменена")


def main() -> None:
    """Run the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    target_filter = filters.Chat(chat_id=int(TARGET_CHAT_ID))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & target_filter,
            handle_message,
        )
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & ~target_filter, echo)
    )

    job_queue = application.job_queue
    job_queue.run_daily(scheduled_post_job, time(hour=10, minute=0))

    application.run_polling()


if __name__ == "__main__":
    main()
