from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv

# Lazy import to avoid the cost if Telegram actions are never triggered
TelethonClient: Optional[object]
try:
    from telethon import TelegramClient as _TelegramClient

    TelethonClient = _TelegramClient  # type: ignore[assignment]
except ModuleNotFoundError:  # telethon is an optional dependency for some commands only
    TelethonClient = None  # pragma: no cover

load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "kachamba_session")
TARGET_DEFAULT = os.getenv("TARGET_CHANNEL_ID") or os.getenv("TARGET_CHAT_ID")

# Internal, lazily-initialised client instance and an asyncio lock for safe reuse
_client: Optional["_TelegramClient"] = None  # type: ignore[name-defined]
_client_lock = asyncio.Lock()


@asynccontextmanager
async def telegram_client() -> "_TelegramClient":  # type: ignore[name-defined]
    """Yield a shared *connected* TelegramClient instance.

    The instance is created on the first use and kept for the whole lifetime of the
    process so that subsequent callers reuse the already-authorised MTProto session.
    """

    if TelethonClient is None:  # pragma: no cover
        raise RuntimeError("telethon package is not installed. Install with extras: `pip install telethon`. ")

    async with _client_lock:  # ensure only one initialiser runs concurrently
        global _client
        if _client is None:
            _client = TelethonClient(SESSION_NAME, API_ID, API_HASH)
            await _client.connect()
    try:
        yield _client  # type: ignore[misc]
    finally:
        # We deliberately keep the connection open for reuse, *do not* disconnect here
        pass


async def send_message(
    text: str,
    image: Optional[str] = None,
    file: Optional[str] = None,
    target: Optional[int | str] = None,
) -> None:
    """Send a message / media to *target* via the shared Telegram client."""

    if target is None and TARGET_DEFAULT is None:
        raise RuntimeError("TARGET not provided and not set via environment variable")

    async with telegram_client() as client:
        tgt = target or int(TARGET_DEFAULT) if TARGET_DEFAULT and TARGET_DEFAULT.isdigit() else target or TARGET_DEFAULT
        if image:
            await client.send_file(tgt, image, caption=text)
        elif file:
            await client.send_file(tgt, file, caption=text)
        else:
            await client.send_message(tgt, text)