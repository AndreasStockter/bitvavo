"""RSI (Relative Strength Index) strategy."""

from __future__ import annotations

from ..models.candle import Candle
from ..models.signal import Signal, SignalType
from .base import ParameterSpec, Strategy


class RSIStrategy(Strategy):
    def __init__(
        self, period: int = 14, overbought: float = 70.0, oversold: float = 30.0
    ) -> None:
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    @property
    def name(self) -> str:
        return "rsi"

    def _calculate_rsi(self, closes: list[float]) -> float | None:
        if len(closes) < self.period + 1:
            return None

        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        recent = deltas[-(self.period) :]

        gains = [d for d in recent if d > 0]
        losses = [-d for d in recent if d < 0]

        avg_gain = sum(gains) / self.period if gains else 0.0
        avg_loss = sum(losses) / self.period if losses else 0.0

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def evaluate(self, candles: list[Candle]) -> Signal:
        closes = [c.close for c in candles]
        rsi = self._calculate_rsi(closes)

        if rsi is None:
            return Signal(SignalType.HOLD, self.name)

        if rsi <= self.oversold:
            return Signal(
                SignalType.BUY, self.name, metadata={"rsi": rsi}
            )
        if rsi >= self.overbought:
            return Signal(
                SignalType.SELL, self.name, metadata={"rsi": rsi}
            )

        return Signal(SignalType.HOLD, self.name, metadata={"rsi": rsi})

    @classmethod
    def parameter_specs(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec("period", 7, 28, 7, 14),
            ParameterSpec("overbought", 65, 80, 5, 70),
            ParameterSpec("oversold", 20, 35, 5, 30),
        ]

    @classmethod
    def from_params(cls, params: dict) -> RSIStrategy:
        return cls(
            period=int(params.get("period", 14)),
            overbought=float(params.get("overbought", 70.0)),
            oversold=float(params.get("oversold", 30.0)),
        )
