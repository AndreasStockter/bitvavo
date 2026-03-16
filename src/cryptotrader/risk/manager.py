"""Risk management module."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from ..config.schema import RiskConfig
from ..models.order import Order, OrderSide
from ..models.portfolio import Portfolio

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RiskDecision:
    allowed: bool
    reason: str = ""
    adjusted_amount: float | None = None


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config
        self._daily_trades: dict[str, int] = {}  # date_str -> count
        self._peak_value: float = 0.0

    def check_order(self, order: Order, portfolio: Portfolio) -> RiskDecision:
        """Check if an order passes all risk checks."""
        # Max daily trades
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_count = self._daily_trades.get(today, 0)
        if daily_count >= self.config.max_daily_trades:
            return RiskDecision(False, f"Max daily trades ({self.config.max_daily_trades}) reached")

        # Max position size
        if order.side == OrderSide.BUY:
            order_value = order.amount * order.price
            total_value = portfolio.total_value
            if total_value > 0 and order_value / total_value > self.config.max_position_pct:
                max_amount = (total_value * self.config.max_position_pct) / order.price
                return RiskDecision(
                    True,
                    f"Position size reduced to {self.config.max_position_pct:.0%}",
                    adjusted_amount=max_amount,
                )

            # Check sufficient cash
            if order_value > portfolio.cash:
                max_amount = portfolio.cash / order.price * 0.99  # small buffer for fees
                if max_amount <= 0:
                    return RiskDecision(False, "Insufficient cash")
                return RiskDecision(True, "Amount reduced to available cash", adjusted_amount=max_amount)

        # Max drawdown check
        total_value = portfolio.total_value
        self._peak_value = max(self._peak_value, total_value)
        if self._peak_value > 0:
            drawdown = (self._peak_value - total_value) / self._peak_value
            if drawdown >= self.config.max_drawdown_pct:
                return RiskDecision(False, f"Max drawdown ({self.config.max_drawdown_pct:.0%}) reached")

        return RiskDecision(True)

    def record_trade(self) -> None:
        """Record a trade for daily counting."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._daily_trades[today] = self._daily_trades.get(today, 0) + 1

    def check_stop_loss(self, entry_price: float, current_price: float) -> bool:
        """Return True if stop loss is triggered."""
        if entry_price <= 0:
            return False
        loss_pct = (entry_price - current_price) / entry_price
        return loss_pct >= self.config.stop_loss_pct

    def check_take_profit(self, entry_price: float, current_price: float) -> bool:
        """Return True if take profit is triggered."""
        if entry_price <= 0:
            return False
        profit_pct = (current_price - entry_price) / entry_price
        return profit_pct >= self.config.take_profit_pct
