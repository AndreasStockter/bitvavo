"""Telegram notification via httpx (Null Object pattern)."""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class Notifier(Protocol):
    async def notify(self, message: str) -> None: ...


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._client = httpx.AsyncClient(timeout=10)

    async def notify(self, message: str) -> None:
        url = f"{TELEGRAM_API}/bot{self._bot_token}/sendMessage"
        try:
            await self._client.post(
                url,
                json={"chat_id": self._chat_id, "text": message, "parse_mode": "Markdown"},
            )
        except Exception:
            logger.exception("Failed to send Telegram notification")

    async def close(self) -> None:
        await self._client.aclose()


class NullNotifier:
    """No-op notifier when Telegram is disabled."""

    async def notify(self, message: str) -> None:
        pass
