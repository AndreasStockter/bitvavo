"""Moving Average Crossover strategy."""

from __future__ import annotations

from ..models.candle import Candle
from ..models.signal import Signal, SignalType
from .base import ParameterSpec, Strategy


class MACrossover(Strategy):
    def __init__(self, fast_period: int = 10, slow_period: int = 30) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period

    @property
    def name(self) -> str:
        return "ma_crossover"

    def evaluate(self, candles: list[Candle]) -> Signal:
        closes = [c.close for c in candles]
        if len(closes) < self.slow_period + 1:
            return Signal(SignalType.HOLD, self.name)

        fast_now = self._sma(closes, self.fast_period)
        slow_now = self._sma(closes, self.slow_period)
        fast_prev = self._sma(closes[:-1], self.fast_period)
        slow_prev = self._sma(closes[:-1], self.slow_period)

        if None in (fast_now, slow_now, fast_prev, slow_prev):
            return Signal(SignalType.HOLD, self.name)

        # Crossover: fast crosses above slow → buy
        if fast_prev <= slow_prev and fast_now > slow_now:
            return Signal(
                SignalType.BUY,
                self.name,
                metadata={"fast_sma": fast_now, "slow_sma": slow_now},
            )
        # Crossunder: fast crosses below slow → sell
        if fast_prev >= slow_prev and fast_now < slow_now:
            return Signal(
                SignalType.SELL,
                self.name,
                metadata={"fast_sma": fast_now, "slow_sma": slow_now},
            )

        return Signal(SignalType.HOLD, self.name)

    @classmethod
    def parameter_specs(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec("fast_period", 5, 25, 5, 10),
            ParameterSpec("slow_period", 20, 60, 5, 30),
        ]

    @classmethod
    def from_params(cls, params: dict) -> MACrossover:
        return cls(
            fast_period=int(params.get("fast_period", 10)),
            slow_period=int(params.get("slow_period", 30)),
        )
