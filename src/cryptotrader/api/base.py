"""TradingClient Protocol - structural subtyping for API clients."""

from __future__ import annotations

from typing import Protocol

from ..models.candle import Candle
from ..models.order import Order


class TradingClient(Protocol):
    async def get_candles(
        self, market: str, interval: str, limit: int = 100
    ) -> list[Candle]: ...

    async def get_ticker_price(self, market: str) -> float: ...

    async def place_order(self, order: Order) -> Order: ...

    async def get_open_orders(self, market: str) -> list[Order]: ...

    async def cancel_order(self, market: str, order_id: str) -> bool: ...

    async def get_balance(self) -> dict[str, float]: ...
