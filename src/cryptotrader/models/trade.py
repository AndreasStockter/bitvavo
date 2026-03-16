"""Trade record data model."""

from __future__ import annotations

from dataclasses import dataclass, field

from .order import OrderSide


@dataclass(slots=True)
class Trade:
    trade_id: str
    market: str
    side: OrderSide
    amount: float
    price: float
    fee: float
    timestamp: int
    strategy_name: str = ""
    pnl: float | None = None
    metadata: dict = field(default_factory=dict)
