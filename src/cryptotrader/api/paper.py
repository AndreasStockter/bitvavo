"""Paper trading client for simulation without real orders."""

from __future__ import annotations

import time
import uuid

from ..models.candle import Candle
from ..models.order import Order, OrderStatus


class PaperTradingClient:
    def __init__(self, initial_balance: float = 10000.0, fee_pct: float = 0.0025) -> None:
        self._balance: dict[str, float] = {"EUR": initial_balance}
        self._orders: list[Order] = []
        self._candle_cache: dict[str, list[Candle]] = {}
        self._fee_pct = fee_pct

    def set_candles(self, market: str, candles: list[Candle]) -> None:
        """Inject candles for testing/backtesting."""
        self._candle_cache[market] = candles

    async def get_candles(
        self, market: str, interval: str, limit: int = 100
    ) -> list[Candle]:
        candles = self._candle_cache.get(market, [])
        return candles[-limit:]

    async def get_ticker_price(self, market: str) -> float:
        candles = self._candle_cache.get(market, [])
        if candles:
            return candles[-1].close
        return 0.0

    async def place_order(self, order: Order) -> Order:
        order.order_id = str(uuid.uuid4())[:8]
        order.timestamp = int(time.time() * 1000)

        # Simulate immediate fill
        base, quote = market_parts(order.market)
        fee = order.amount * order.price * self._fee_pct
        order.fee = fee

        if order.side.value == "buy":
            cost = order.amount * order.price + fee
            if self._balance.get(quote, 0) >= cost:
                self._balance[quote] = self._balance.get(quote, 0) - cost
                self._balance[base] = self._balance.get(base, 0) + order.amount
                order.status = OrderStatus.FILLED
                order.filled_amount = order.amount
            else:
                order.status = OrderStatus.REJECTED
        else:  # sell
            if self._balance.get(base, 0) >= order.amount:
                self._balance[base] = self._balance.get(base, 0) - order.amount
                self._balance[quote] = (
                    self._balance.get(quote, 0) + order.amount * order.price - fee
                )
                order.status = OrderStatus.FILLED
                order.filled_amount = order.amount
            else:
                order.status = OrderStatus.REJECTED

        if order.status == OrderStatus.FILLED:
            self._orders.append(order)

        return order

    async def get_open_orders(self, market: str) -> list[Order]:
        return []  # Paper trading fills immediately

    async def cancel_order(self, market: str, order_id: str) -> bool:
        return True

    async def get_balance(self) -> dict[str, float]:
        return dict(self._balance)


def market_parts(market: str) -> tuple[str, str]:
    """Split 'BTC-EUR' into ('BTC', 'EUR')."""
    parts = market.split("-")
    return parts[0], parts[1] if len(parts) > 1 else "EUR"
