"""Async wrapper around the synchronous Bitvavo SDK using asyncio.to_thread."""

from __future__ import annotations

import asyncio
import logging
import time

from ..models.candle import Candle
from ..models.order import Order, OrderSide, OrderStatus

logger = logging.getLogger(__name__)


class AsyncBitvavoClient:
    def __init__(self, api_key: str, api_secret: str) -> None:
        from python_bitvavo_api.bitvavo import Bitvavo

        self._bitvavo = Bitvavo(
            {"APIKEY": api_key, "APISECRET": api_secret, "RESTURL": "https://api.bitvavo.com/v2"}
        )

    async def get_candles(
        self, market: str, interval: str, limit: int = 100
    ) -> list[Candle]:
        response = await asyncio.to_thread(
            self._bitvavo.candles, market, interval, {"limit": limit}
        )
        if isinstance(response, dict) and "error" in response:
            logger.error("Bitvavo candles error: %s", response)
            return []
        candles = [Candle.from_bitvavo(c) for c in response]
        candles.sort(key=lambda c: c.timestamp)
        return candles

    async def get_ticker_price(self, market: str) -> float:
        response = await asyncio.to_thread(
            self._bitvavo.tickerPrice, {"market": market}
        )
        if isinstance(response, dict) and "error" in response:
            logger.error("Bitvavo ticker error: %s", response)
            return 0.0
        return float(response.get("price", 0))

    async def place_order(self, order: Order) -> Order:
        body = {
            "market": order.market,
            "side": order.side.value,
            "orderType": "limit",
            "price": str(order.price),
            "amount": str(order.amount),
        }
        response = await asyncio.to_thread(
            self._bitvavo.placeOrder, order.market, order.side.value, "limit", body
        )
        if isinstance(response, dict) and "error" in response:
            logger.error("Bitvavo place order error: %s", response)
            order.status = OrderStatus.REJECTED
            return order

        order.order_id = response.get("orderId", "")
        order.status = OrderStatus(response.get("status", "new"))
        order.timestamp = int(time.time() * 1000)
        order.filled_amount = float(response.get("filledAmount", 0))
        return order

    async def get_open_orders(self, market: str) -> list[Order]:
        response = await asyncio.to_thread(
            self._bitvavo.ordersOpen, {"market": market}
        )
        if isinstance(response, dict) and "error" in response:
            logger.error("Bitvavo open orders error: %s", response)
            return []
        orders = []
        for o in response:
            orders.append(
                Order(
                    market=o["market"],
                    side=OrderSide(o["side"]),
                    amount=float(o["amount"]),
                    price=float(o["price"]),
                    order_id=o["orderId"],
                    status=OrderStatus(o.get("status", "new")),
                    timestamp=o.get("created", 0),
                    filled_amount=float(o.get("filledAmount", 0)),
                )
            )
        return orders

    async def cancel_order(self, market: str, order_id: str) -> bool:
        response = await asyncio.to_thread(
            self._bitvavo.cancelOrder, market, order_id
        )
        if isinstance(response, dict) and "error" in response:
            logger.error("Bitvavo cancel error: %s", response)
            return False
        return True

    async def get_balance(self) -> dict[str, float]:
        response = await asyncio.to_thread(self._bitvavo.balance, {})
        if isinstance(response, dict) and "error" in response:
            logger.error("Bitvavo balance error: %s", response)
            return {}
        return {item["symbol"]: float(item["available"]) for item in response}
