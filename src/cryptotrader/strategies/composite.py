"""Composite strategy combining multiple strategies."""

from __future__ import annotations

from collections import Counter

from ..models.candle import Candle
from ..models.signal import Signal, SignalType
from .base import ParameterSpec, Strategy


class CompositeStrategy(Strategy):
    """Combines multiple strategies with configurable voting mode."""

    def __init__(
        self, strategies: list[Strategy], mode: str = "majority"
    ) -> None:
        self.strategies = strategies
        self.mode = mode  # "unanimous", "majority", "any"

    @property
    def name(self) -> str:
        names = "+".join(s.name for s in self.strategies)
        return f"composite({names})"

    def evaluate(self, candles: list[Candle]) -> Signal:
        signals = [s.evaluate(candles) for s in self.strategies]
        actionable = [s for s in signals if s.is_actionable]

        if not actionable:
            return Signal(SignalType.HOLD, self.name)

        type_counts = Counter(s.signal_type for s in actionable)

        if self.mode == "unanimous":
            if len(type_counts) == 1 and len(actionable) == len(self.strategies):
                chosen = actionable[0].signal_type
            else:
                return Signal(SignalType.HOLD, self.name)
        elif self.mode == "any":
            chosen = type_counts.most_common(1)[0][0]
        else:  # majority
            most_common_type, count = type_counts.most_common(1)[0]
            if count > len(self.strategies) / 2:
                chosen = most_common_type
            else:
                return Signal(SignalType.HOLD, self.name)

        confidence = type_counts[chosen] / len(self.strategies)
        return Signal(
            chosen,
            self.name,
            confidence=confidence,
            metadata={"votes": dict(type_counts), "signals": [s.signal_type.value for s in signals]},
        )

    @classmethod
    def parameter_specs(cls) -> list[ParameterSpec]:
        return []

    @classmethod
    def from_params(cls, params: dict) -> CompositeStrategy:
        return cls(strategies=params.get("strategies", []), mode=params.get("mode", "majority"))
