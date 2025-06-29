import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

import openai

# Logging configuration
logger = logging.getLogger(__name__)
if not logger.handlers:
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

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stderr_handler)


def load_identity(path: Optional[str] = None) -> str:
    """Load bot identity text from a file."""
    path = path or os.getenv("IDENTITY_FILE", "kachamba_identity.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Не найден файл идентичности: %s", path)
        return ""


def get_scheduled_theme(path: Optional[str] = None) -> Optional[str]:
    """Return today's theme from schedule file if available."""
    path = path or os.getenv("THEME_SCHEDULE_FILE", "theme_schedule.txt")
    day = datetime.today().strftime("%A").lower()
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.lower().startswith(day + ":"):
                    return line.split(":", 1)[1].strip()
    except FileNotFoundError:
        logger.warning("Не найден файл расписания: %s", path)
    return None


def is_unique(post: str, path: Optional[str] = None) -> bool:
    """Check that post text is not already present in history file."""
    path = path or os.getenv("POST_HISTORY_FILE", "post_history.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return post.strip() not in f.read()
    except FileNotFoundError:
        return True


def save_history(post: str, path: Optional[str] = None) -> None:
    """Save generated post to history file and update last post."""
    history_path = path or os.getenv("POST_HISTORY_FILE", "post_history.txt")
    last_path = os.getenv("LAST_POST_FILE", "last_post.txt")
    ts = datetime.now().isoformat()
    with open(history_path, "a", encoding="utf-8") as f:
        f.write(f"{ts}\n{post}\n{'=' * 40}\n")
    with open(last_path, "w", encoding="utf-8") as f:
        f.write(post)


def generate_ai_response(prompt_text: str) -> str:
    """Generate a response from OpenAI using loaded identity."""
    identity = load_identity()
    messages = [
        {"role": "system", "content": identity},
        {"role": "user", "content": prompt_text},
    ]
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.8,
        )
        return resp.choices[0].message.content
    except Exception as exc:  # OpenAI raises several exception types
        logger.error("OpenAI API request failed: %s", exc)
        raise
