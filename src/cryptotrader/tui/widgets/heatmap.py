"""Heatmap widget for backtest parameter sweep results."""

from __future__ import annotations

from rich.table import Table
from rich.text import Text
from textual.widgets import Static

from ...models.backtest import SweepResult


class HeatmapWidget(Static):
    """Displays parameter sweep results as a heatmap table."""

    DEFAULT_CSS = """
    HeatmapWidget {
        height: auto;
        margin: 1;
        padding: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("Run a sweep to see results.", **kwargs)

    def update_results(self, sweep: SweepResult) -> None:
        if not sweep.results or len(sweep.param_grid) < 2:
            self.update("Not enough parameters for heatmap")
            return

        param_names = list(sweep.param_grid.keys())
        row_param = param_names[0]
        col_param = param_names[1]

        row_values = sorted(set(r.params.get(row_param) for r in sweep.results))
        col_values = sorted(set(r.params.get(col_param) for r in sweep.results))

        # Build lookup
        lookup: dict[tuple, float] = {}
        all_sharpes = []
        for r in sweep.results:
            key = (r.params.get(row_param), r.params.get(col_param))
            lookup[key] = r.sharpe_ratio
            all_sharpes.append(r.sharpe_ratio)

        min_sharpe = min(all_sharpes) if all_sharpes else 0
        max_sharpe = max(all_sharpes) if all_sharpes else 1

        table = Table(title=f"Sharpe Ratio Heatmap ({row_param} x {col_param})")
        table.add_column(row_param, style="bold")
        for cv in col_values:
            table.add_column(str(cv), justify="center")

        for rv in row_values:
            cells = []
            for cv in col_values:
                sharpe = lookup.get((rv, cv), 0)
                cells.append(self._color_cell(sharpe, min_sharpe, max_sharpe))
            table.add_row(str(rv), *cells)

        self.update(table)

    def _color_cell(self, value: float, min_val: float, max_val: float) -> Text:
        """Color a cell based on its value relative to min/max."""
        if max_val == min_val:
            norm = 0.5
        else:
            norm = (value - min_val) / (max_val - min_val)

        if norm >= 0.66:
            style = "bold green"
        elif norm >= 0.33:
            style = "yellow"
        else:
            style = "red"

        return Text(f"{value:.2f}", style=style)
