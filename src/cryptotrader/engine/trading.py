"""Trading engine orchestrator."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from ..api.base import TradingClient
from ..config.schema import AppConfig
from ..db.repository import TradeRepository
from ..models.order import Order, OrderSide, OrderStatus
from ..models.portfolio import Portfolio
from ..models.signal import Signal, SignalType
from ..models.trade import Trade
from ..notifications.telegram import Notifier
from ..risk.manager import RiskManager
from ..strategies.base import Strategy

logger = logging.getLogger(__name__)


class TradingEngine:
    def __init__(
        self,
        config: AppConfig,
        client: TradingClient,
        strategy: Strategy,
        risk_manager: RiskManager,
        repository: TradeRepository,
        notifier: Notifier,
    ) -> None:
        self.config = config
        self.client = client
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.repository = repository
        self.notifier = notifier
        self.portfolio = Portfolio()
        self._callbacks: list[Any] = []

    def add_callback(self, callback: Any) -> None:
        self._callbacks.append(callback)

    async def _notify_callbacks(self, event: str, data: Any = None) -> None:
        for cb in self._callbacks:
            try:
                await cb(event, data)
            except Exception:
                logger.exception("Callback error for event %s", event)

    async def initialize(self) -> None:
        """Initialize portfolio from exchange balance."""
        balance = await self.client.get_balance()
        market = self.config.trading.market
        base, quote = market.split("-")
        self.portfolio.cash = balance.get(quote, 0.0)
        base_amount = balance.get(base, 0.0)
        if base_amount > 0:
            price = await self.client.get_ticker_price(market)
            pos = self.portfolio.get_position(market)
            pos.amount = base_amount
            pos.current_price = price
            pos.avg_entry_price = price  # approximation
        await self._notify_callbacks("initialized", self.portfolio)

    async def tick(self) -> None:
        """Execute one trading cycle."""
        market = self.config.trading.market
        interval = self.config.trading.interval

        candles = await self.client.get_candles(market, interval)
        if not candles:
            logger.warning("No candles received for %s", market)
            return

        # Update current price
        current_price = candles[-1].close
        pos = self.portfolio.get_position(market)
        pos.current_price = current_price
        await self._notify_callbacks("price_update", {
            "market": market, "price": current_price, "portfolio": self.portfolio
        })

        # Check stop loss / take profit
        if pos.amount > 0:
            if self.risk_manager.check_stop_loss(pos.avg_entry_price, current_price):
                logger.info("Stop loss triggered at %.2f", current_price)
                await self._execute_sell(market, pos.amount, current_price, "stop_loss")
                return
            if self.risk_manager.check_take_profit(pos.avg_entry_price, current_price):
                logger.info("Take profit triggered at %.2f", current_price)
                await self._execute_sell(market, pos.amount, current_price, "take_profit")
                return

        # Evaluate strategy
        signal = self.strategy.evaluate(candles)
        await self._notify_callbacks("signal", signal)

        if not signal.is_actionable:
            return

        if signal.signal_type == SignalType.BUY:
            await self._handle_buy(market, current_price, signal)
        elif signal.signal_type == SignalType.SELL:
            if pos.amount > 0:
                await self._execute_sell(market, pos.amount, current_price, "signal")

    async def _handle_buy(self, market: str, price: float, signal: Signal) -> None:
        amount = (self.portfolio.cash * 0.95) / price
        if amount <= 0:
            return

        order = Order(market=market, side=OrderSide.BUY, amount=amount, price=price)
        decision = self.risk_manager.check_order(order, self.portfolio)

        if not decision.allowed:
            logger.info("Risk check blocked buy: %s", decision.reason)
            await self._notify_callbacks("risk_blocked", decision)
            return

        if decision.adjusted_amount is not None:
            order.amount = decision.adjusted_amount

        filled_order = await self.client.place_order(order)

        if filled_order.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED):
            actual_amount = filled_order.filled_amount or filled_order.amount
            self.portfolio.update_position(
                market, actual_amount, price, filled_order.fee
            )
            self.risk_manager.record_trade()
            trade = Trade(
                trade_id=filled_order.order_id or str(uuid.uuid4())[:8],
                market=market,
                side=OrderSide.BUY,
                amount=actual_amount,
                price=price,
                fee=filled_order.fee,
                timestamp=filled_order.timestamp or int(time.time() * 1000),
                strategy_name=self.strategy.name,
            )
            await self.repository.insert(trade)
            msg = f"BUY {actual_amount:.6f} {market} @ {price:.2f}"
            await self.notifier.notify(msg)
            await self._notify_callbacks("trade", trade)

    async def _execute_sell(
        self, market: str, amount: float, price: float, reason: str
    ) -> None:
        order = Order(market=market, side=OrderSide.SELL, amount=amount, price=price)
        filled_order = await self.client.place_order(order)

        if filled_order.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED):
            actual_amount = filled_order.filled_amount or filled_order.amount
            pos = self.portfolio.get_position(market)
            pnl = (price - pos.avg_entry_price) * actual_amount - filled_order.fee
            self.portfolio.update_position(
                market, -actual_amount, price, filled_order.fee
            )
            self.risk_manager.record_trade()
            trade = Trade(
                trade_id=filled_order.order_id or str(uuid.uuid4())[:8],
                market=market,
                side=OrderSide.SELL,
                amount=actual_amount,
                price=price,
                fee=filled_order.fee,
                timestamp=filled_order.timestamp or int(time.time() * 1000),
                strategy_name=self.strategy.name,
                pnl=pnl,
                metadata={"reason": reason},
            )
            await self.repository.insert(trade)
            msg = f"SELL {actual_amount:.6f} {market} @ {price:.2f} | PnL: {pnl:.2f} ({reason})"
            await self.notifier.notify(msg)
            await self._notify_callbacks("trade", trade)
