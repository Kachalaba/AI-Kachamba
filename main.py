from telethon.sync import TelegramClient
from telethon.tl.functions.messages import SendMessageRequest
from dotenv import load_dotenv
import openai
import os

# Загрузка переменных из .env
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
openai.api_key = os.getenv("OPENAI_KEY")

# Целевая цель (можно заменить на username, chat_id, канал)
TARGET = "me"  # Для теста — сообщение себе

def generate_post():
    prompt = "Напиши короткий, стильный пост о восстановлении после тренировок. Без банальщины, до 800 символов."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты спортивный Telegram-блогер, пишешь лаконичные, умные посты с харизмой."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

with TelegramClient('kachamba_session', api_id, api_hash) as client:
    post = generate_post()
    client.send_message(TARGET, post)
    print("Пост отправлен себе. Проверь Telegram.")
