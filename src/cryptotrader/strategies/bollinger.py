"""Bollinger Bands strategy."""

from __future__ import annotations

from ..models.candle import Candle
from ..models.signal import Signal, SignalType
from .base import ParameterSpec, Strategy


class BollingerBands(Strategy):
    def __init__(self, period: int = 20, std_dev: float = 2.0) -> None:
        self.period = period
        self.std_dev = std_dev

    @property
    def name(self) -> str:
        return "bollinger"

    def evaluate(self, candles: list[Candle]) -> Signal:
        closes = [c.close for c in candles]
        if len(closes) < self.period:
            return Signal(SignalType.HOLD, self.name)

        sma = self._sma(closes, self.period)
        std = self._std(closes, self.period)

        if sma is None or std is None:
            return Signal(SignalType.HOLD, self.name)

        upper = sma + self.std_dev * std
        lower = sma - self.std_dev * std
        current = closes[-1]

        meta = {"upper": upper, "lower": lower, "sma": sma, "price": current}

        if current <= lower:
            return Signal(SignalType.BUY, self.name, metadata=meta)
        if current >= upper:
            return Signal(SignalType.SELL, self.name, metadata=meta)

        return Signal(SignalType.HOLD, self.name, metadata=meta)

    @classmethod
    def parameter_specs(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec("period", 10, 30, 5, 20),
            ParameterSpec("std_dev", 1.5, 3.0, 0.5, 2.0),
        ]

    @classmethod
    def from_params(cls, params: dict) -> BollingerBands:
        return cls(
            period=int(params.get("period", 20)),
            std_dev=float(params.get("std_dev", 2.0)),
        )
