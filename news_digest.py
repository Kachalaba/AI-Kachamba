import openai
import os
import feedparser
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from datetime import datetime

load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
openai.api_key = os.getenv("OPENAI_KEY")

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

def generate_digest(system_prompt, news_prompt, news_text):
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": news_prompt + "\n\nОсь новини:\n" + news_text}
        ]
    )
    return response.choices[0].message.content.strip()

def send_to_telegram(message, target):
    with TelegramClient('kachamba_session', api_id, api_hash) as client:
        client.send_message(target, message)
        print(f"✅ Дайджест відправлено у {target}")

def main():
    news_text = fetch_news()
    identity = load_file("C:\\Users\\user\\Desktop\\KachalabaGP\\lowpulse\\kachamba_identity.txt")
    news_prompt = load_file("C:\\Users\\user\\Desktop\\KachalabaGP\\lowpulse\\prompts\\news.txt")
    digest = generate_digest(identity, news_prompt, news_text)

    with open("C:\\Users\\user\\Desktop\\KachalabaGP\\lowpulse\\last_news_digest.txt", "w", encoding="utf-8") as f:
        f.write(digest)

    preview_message = (
        "🗞️ *Щотижневий дайджест Low Pulse:*\n\n"
        + digest
        + "\n\n⚠️ Перед публікацією перевір стиль, фактологію і подачу."
    )
    send_to_telegram(preview_message, PREVIEW_TARGET)

if __name__ == "__main__":
    main()