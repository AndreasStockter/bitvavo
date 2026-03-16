"""Async trading loop."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .trading import TradingEngine

logger = logging.getLogger(__name__)

INTERVAL_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "6h": 21600,
    "8h": 28800,
    "12h": 43200,
    "1d": 86400,
}


class TradingLoop:
    def __init__(self, engine: TradingEngine, interval: str = "1h") -> None:
        self.engine = engine
        self.interval = interval
        self._running = False
        self._task: asyncio.Task | None = None
        self._callbacks: list[Any] = []

    @property
    def is_running(self) -> bool:
        return self._running

    def add_callback(self, callback: Any) -> None:
        self._callbacks.append(callback)

    async def start(self) -> None:
        """Start the trading loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Trading loop started (interval: %s)", self.interval)

    async def stop(self) -> None:
        """Stop the trading loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Trading loop stopped")

    async def _loop(self) -> None:
        sleep_seconds = INTERVAL_SECONDS.get(self.interval, 3600)

        # Initial tick immediately
        await self._safe_tick()

        while self._running:
            await asyncio.sleep(sleep_seconds)
            if self._running:
                await self._safe_tick()

    async def _safe_tick(self) -> None:
        try:
            await self.engine.tick()
            for cb in self._callbacks:
                try:
                    await cb("tick_complete", None)
                except Exception:
                    logger.exception("Loop callback error")
        except Exception:
            logger.exception("Trading tick error")
