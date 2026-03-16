"""Order data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    NEW = "new"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(slots=True)
class Order:
    market: str
    side: OrderSide
    amount: float
    price: float
    order_id: str = ""
    status: OrderStatus = OrderStatus.NEW
    timestamp: int = 0
    filled_amount: float = 0.0
    fee: float = 0.0
    metadata: dict = field(default_factory=dict)
