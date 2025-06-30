# ruff: noqa: D401

import argparse
import asyncio
import logging
import os
from datetime import datetime

from dotenv import load_dotenv

from ai_utils import (
    async_chat_completion,
    get_scheduled_theme,
    is_unique,
    load_identity,
    save_history,
)
from telegram_client import send_message

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Загрузка .env
load_dotenv()
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "autopost")
TARGET = int(os.getenv("TARGET_CHANNEL_ID", 0))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
THEME_SCHEDULE_FILE = os.getenv("THEME_SCHEDULE_FILE", "theme_schedule.txt")
IDENTITY_FILE = os.getenv("IDENTITY_FILE", "kachamba_identity.txt")
POST_HISTORY_FILE = os.getenv("POST_HISTORY_FILE", "post_history.txt")
LAST_POST_FILE = os.getenv("LAST_POST_FILE", "last_post.txt")

openai.api_key = OPENAI_API_KEY


# Генерация через OpenAI (асинхронно)
async def generate_post_async(
    theme: str,
    tone: str,
    length: str,
    hashtags: str | None,
    mention: str | None,
    model: str,
    temp: float,
) -> str:
    """Generate post content asynchronously using OpenAI."""

    identity = load_identity()
    user_content = f"Тема: {theme}\nТон: {tone}\nДлина: {length}"
    if hashtags:
        user_content += f"\nХэштеги: {hashtags}"
    if mention:
        user_content += f"\nУпоминання: {mention}"

    messages = [
        {"role": "system", "content": identity},
        {"role": "user", "content": user_content},
    ]
    logging.info("GPT запрос: тема=%s, тон=%s, длина=%s", theme, tone, length)
    return await async_chat_completion(messages, model=model, temperature=temp)


# Телеграм отправка через пул клиента
async def send_to_telegram(text: str, image: str | None, file: str | None):
    try:
        await send_message(text, image=image, file=file)
    except Exception as exc:  # noqa: BLE001
        logging.error("Telegram error: %s", exc)


# Парсинг времени отправки
def schedule_delay(send_at, delay):
    if send_at:
        dt = datetime.fromisoformat(send_at)
        return max((dt - datetime.now()).total_seconds(), 0)
    if delay:
        return delay
    return 0


# CLI
def parse_args():
    p = argparse.ArgumentParser(description="VIP Autopost Low Pulse")
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--schedule", action="store_true")
    grp.add_argument("--theme", type=str)
    p.add_argument(
        "--tone", choices=["serious", "funny", "ironical"], default="serious"
    )
    p.add_argument("--length", choices=["short", "medium", "long"], default="medium")
    p.add_argument("--hashtags", type=str, help='"#tag1,#tag2"')
    p.add_argument("--mention", type=str, help="@username")
    p.add_argument("--image", type=str, help="path to image")
    p.add_argument("--file", type=str, help="path to file")
    p.add_argument("--model", type=str, default="gpt-4.1")
    p.add_argument("--temp", type=float, default=0.9)
    p.add_argument("--send-at", type=str, help="YYYY-MM-DDTHH:MM:SS")
    p.add_argument("--delay", type=int, help="seconds to wait")
    return p.parse_args()


# Main coroutine
async def autopost_flow(args):
    theme = get_scheduled_theme() if args.schedule else args.theme
    if not theme:
        logging.error("Тема не указана или не найдена.")
        return

    post = await generate_post_async(
        theme,
        args.tone,
        args.length,
        args.hashtags,
        args.mention,
        args.model,
        args.temp,
    )

    if not is_unique(post):
        logging.warning("Дубликат, отменяем.")
        return

    wait = schedule_delay(args.send_at, args.delay)
    if wait > 0:
        logging.info("Ждём %s секунд перед отправкой...", wait)
        await asyncio.sleep(wait)

    await send_to_telegram(post, args.image, args.file)
    save_history(post)
    logging.info("VIP пост отправлен и сохранён.")


def main():  # entry point kept for backward compatibility
    asyncio.run(autopost_flow(parse_args()))


if __name__ == "__main__":
    main()
