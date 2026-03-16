"""Base strategy classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..models.candle import Candle
from ..models.signal import Signal


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    name: str
    min_value: float
    max_value: float
    step: float
    default: float

    def values(self) -> list[float]:
        result = []
        v = self.min_value
        while v <= self.max_value + 1e-9:
            result.append(v)
            v += self.step
        return result


class Strategy(ABC):
    """Base class for all trading strategies."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def evaluate(self, candles: list[Candle]) -> Signal:
        """Evaluate candles and return a trading signal."""
        ...

    @classmethod
    @abstractmethod
    def parameter_specs(cls) -> list[ParameterSpec]:
        """Return parameter specifications for backtesting sweeps."""
        ...

    @classmethod
    @abstractmethod
    def from_params(cls, params: dict) -> Strategy:
        """Create strategy instance from parameter dict."""
        ...

    def _sma(self, values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        return sum(values[-period:]) / period

    def _ema(self, values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period
        for val in values[period:]:
            ema = (val - ema) * multiplier + ema
        return ema

    def _std(self, values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        window = values[-period:]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        return variance**0.5
