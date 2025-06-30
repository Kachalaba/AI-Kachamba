import os
from datetime import datetime

import feedparser
from dotenv import load_dotenv

from ai_utils import generate_ai_response as generate_ai_response_async
from telegram_client import send_message

load_dotenv()
api_id = int(os.getenv("API_ID", 0))
api_hash = os.getenv("API_HASH", "")

MODEL = "gpt-4"
PREVIEW_TARGET = "me"
RSS_URL = "https://swimswam.com/feed/"

def fetch_news(limit=5):
    feed = feedparser.parse(RSS_URL)
    entries = feed.entries[:limit]
    news_items = []
    for entry in entries:
        title = entry.title
        link = entry.link
        news_items.append(f"- {title}\n{link}")
    return "\n".join(news_items)

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

async def generate_digest(system_prompt, news_prompt, news_text):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": news_prompt + "\n\nОсь новини:\n" + news_text},
    ]
    return await generate_ai_response_async("\n".join([system_prompt, news_prompt, news_text]))

async def send_to_telegram(message, target):
    await send_message(message, target=target)

async def main_async():
    news_text = fetch_news()
    identity = load_file("kachamba_identity.txt")
    news_prompt = load_file("news.txt") if os.path.exists("news.txt") else "Згенеруй дайджест."
    digest = await generate_digest(identity, news_prompt, news_text)

    with open("last_news_digest.txt", "w", encoding="utf-8") as f:
        f.write(digest)

    preview_message = (
        "🗞️ *Щотижневий дайджест Low Pulse:*\n\n" + digest + "\n\n⚠️ Перед публікацією перевір стиль, фактологію і подачу."
    )
    await send_to_telegram(preview_message, PREVIEW_TARGET)

def main():
    import asyncio

    asyncio.run(main_async())

if __name__ == "__main__":
    main()