"""OHLCV candle data model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: int  # milliseconds since epoch
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_bitvavo(cls, raw: list) -> Candle:
        """Create Candle from Bitvavo API response format [timestamp, open, high, low, close, volume]."""
        return cls(
            timestamp=int(raw[0]),
            open=float(raw[1]),
            high=float(raw[2]),
            low=float(raw[3]),
            close=float(raw[4]),
            volume=float(raw[5]),
        )
