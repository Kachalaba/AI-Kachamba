from telethon.sync import TelegramClient
from dotenv import load_dotenv
import os

# Загружаем API_ID и API_HASH из .env
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_file = "kachamba_session"

with TelegramClient(session_file, api_id, api_hash) as client:
    print("🔍 Всі доступні діалоги:\n")
    for dialog in client.iter_dialogs():
        print(f"{dialog.name} — {dialog.id}")