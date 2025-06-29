
import os
import argparse
import asyncio
import logging
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import RPCError
import openai

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Загрузка .env
load_dotenv()
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
SESSION_NAME = os.getenv('SESSION_NAME', 'autopost')
TARGET = int(os.getenv('TARGET_CHANNEL_ID', 0))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
THEME_SCHEDULE_FILE = os.getenv('THEME_SCHEDULE_FILE', 'theme_schedule.txt')
IDENTITY_FILE = os.getenv('IDENTITY_FILE', 'kachamba_identity.txt')
POST_HISTORY_FILE = os.getenv('POST_HISTORY_FILE', 'post_history.txt')
LAST_POST_FILE = os.getenv('LAST_POST_FILE', 'last_post.txt')

openai.api_key = OPENAI_API_KEY

# Получить тему
def get_scheduled_theme(path=THEME_SCHEDULE_FILE):
    day = date.today().strftime('%A').lower()
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                if line.lower().startswith(day + ':'):
                    return line.split(':',1)[1].strip()
    except FileNotFoundError:
        logging.warning(f"Не найден файл расписания: {path}")
    return None

# Загрузить профиль
def load_identity(path=IDENTITY_FILE):
    try:
        return open(path, encoding='utf-8').read()
    except FileNotFoundError:
        logging.warning(f"Не найден файл идентичности: {path}")
        return ''

# Уникальность
def is_unique(post, path=POST_HISTORY_FILE):
    try:
        return post.strip() not in open(path, encoding='utf-8').read()
    except FileNotFoundError:
        return True

# Сохранение
def save_history(post):
    ts = datetime.now().isoformat()
    with open(POST_HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{ts}\n{post}\n{'='*40}\n")
    with open(LAST_POST_FILE, 'w', encoding='utf-8') as f:
        f.write(post)

# Генерация через OpenAI
def generate_post(theme, tone, length, hashtags, mention, model, temp):
    identity = load_identity()
    user_content = f"Тема: {theme}\nТон: {tone}\nДлина: {length}"
    if hashtags:
        user_content += f"\nХэштеги: {hashtags}"
    if mention:
        user_content += f"\nУпоминання: {mention}"
    messages = [
        {"role":"system","content":identity},
        {"role":"user","content":user_content}
    ]
    logging.info(f"GPT запрос: тема={theme}, тон={tone}, длина={length}")
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temp
    )
    return resp.choices[0].message.content

# Отправка Telegram
async def send_to_telegram(text, image, file):
    try:
        async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
            if image:
                await client.send_file(TARGET, image, caption=text)
            elif file:
                await client.send_file(TARGET, file, caption=text)
            else:
                await client.send_message(TARGET, text)
    except RPCError as e:
        logging.error(f"Telegram error: {e}")

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
    grp.add_argument('--schedule', action='store_true')
    grp.add_argument('--theme', type=str)
    p.add_argument('--tone', choices=['serious','funny','ironical'], default='serious')
    p.add_argument('--length', choices=['short','medium','long'], default='medium')
    p.add_argument('--hashtags', type=str, help='"#tag1,#tag2"')
    p.add_argument('--mention', type=str, help='@username')
    p.add_argument('--image', type=str, help='path to image')
    p.add_argument('--file', type=str, help='path to file')
    p.add_argument('--model', type=str, default='gpt-4.1')
    p.add_argument('--temp', type=float, default=0.9)
    p.add_argument('--send-at', type=str, help='YYYY-MM-DDTHH:MM:SS')
    p.add_argument('--delay', type=int, help='seconds to wait')
    return p.parse_args()

# Main
def main():
    args = parse_args()
    theme = get_scheduled_theme() if args.schedule else args.theme
    if not theme:
        logging.error("Тема не указана или не найдена.")
        return
    post = generate_post(
        theme, args.tone, args.length,
        args.hashtags, args.mention,
        args.model, args.temp
    )
    if not is_unique(post):
        logging.warning("Дубликат, отменяем.")
        return
    wait = schedule_delay(args.send_at, args.delay)
    if wait > 0:
        logging.info(f"Ждём {wait} секунд перед отправкой...")
        asyncio.run(asyncio.sleep(wait))
    asyncio.run(send_to_telegram(post, args.image, args.file))
    save_history(post)
    logging.info("VIP пост отправлен и сохранён.")

if __name__ == '__main__':
    main()
