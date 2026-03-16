"""Sparkline price chart widget."""

from __future__ import annotations

from textual.widgets import Sparkline


class PriceChartWidget(Sparkline):
    """A sparkline widget showing price history."""

    DEFAULT_CSS = """
    PriceChartWidget {
        height: 5;
        margin: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(data=[], **kwargs)

    def update_prices(self, prices: list[float]) -> None:
        self.data = prices
