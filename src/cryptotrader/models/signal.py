"""Trading signal data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True, slots=True)
class Signal:
    signal_type: SignalType
    strategy_name: str
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)

    @property
    def is_actionable(self) -> bool:
        return self.signal_type != SignalType.HOLD
