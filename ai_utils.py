import logging
import os
from datetime import datetime
from functools import lru_cache
from logging.handlers import RotatingFileHandler
from typing import List, Optional

# Lazy OpenAI import to improve cold-start performance
_openai = None  # type: ignore


def _get_openai():
    global _openai  # noqa: PLW0603
    if _openai is None:
        import openai  # type: ignore

        openai.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        _openai = openai
    return _openai


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


@lru_cache(maxsize=1)
def load_identity(path: Optional[str] = None) -> str:
    """Load bot identity text from a file. Cached on first read."""

    path = path or os.getenv("IDENTITY_FILE", "kachamba_identity.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Не найден файл идентичности: %s", path)
        return ""


@lru_cache(maxsize=1)
def get_scheduled_theme(path: Optional[str] = None) -> Optional[str]:
    """Return today's theme from schedule file if available. Cached per process."""

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


async def async_chat_completion(
    messages: List[dict],
    model: str = "gpt-4",
    temperature: float = 0.8,
) -> str:
    """Async wrapper around OpenAI ChatCompletion that works for both v0 & v1 SDKs."""

    openai = _get_openai()
    try:
        # New client-style API (>=1.0.0)
        if hasattr(openai, "AsyncOpenAI"):
            client = openai.AsyncOpenAI()
            resp = await client.chat.completions.create(
                model=model, messages=messages, temperature=temperature
            )
            return resp.choices[0].message.content  # type: ignore[index]
        # Legacy coroutine API (<1.0.0)
        resp = await openai.ChatCompletion.acreate(  # type: ignore[attr-defined]
            model=model, messages=messages, temperature=temperature
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        logger.error("OpenAI API request failed: %s", exc)
        raise


async def generate_ai_response(prompt_text: str) -> str:  # backwards-compatible alias
    """Generate a response from OpenAI asynchronously using loaded identity."""

    identity = load_identity()
    messages = [
        {"role": "system", "content": identity},
        {"role": "user", "content": prompt_text},
    ]
    return await async_chat_completion(messages)
