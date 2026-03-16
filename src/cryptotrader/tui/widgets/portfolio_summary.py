"""Portfolio summary widget."""

from __future__ import annotations

from rich.table import Table
from textual.widgets import Static

from ...models.portfolio import Portfolio


class PortfolioSummaryWidget(Static):
    """Shows portfolio cash, positions, and total value."""

    DEFAULT_CSS = """
    PortfolioSummaryWidget {
        height: auto;
        margin: 1;
        padding: 1;
        border: solid $accent;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("Waiting for data...", **kwargs)
        self._portfolio: Portfolio | None = None

    def update_portfolio(self, portfolio: Portfolio) -> None:
        self._portfolio = portfolio
        self._render_table()

    def _render_table(self) -> None:
        if self._portfolio is None:
            self.update("No portfolio data")
            return

        table = Table(title="Portfolio", expand=True)
        table.add_column("Asset", style="cyan")
        table.add_column("Amount", style="green", justify="right")
        table.add_column("Value", style="yellow", justify="right")
        table.add_column("PnL", justify="right")

        table.add_row(
            "Cash (EUR)", "", f"{self._portfolio.cash:,.2f}", ""
        )

        for market, pos in self._portfolio.positions.items():
            if pos.amount > 0:
                pnl = pos.unrealized_pnl
                pnl_style = "green" if pnl >= 0 else "red"
                pnl_str = f"[{pnl_style}]{pnl:+,.2f}[/]"
                table.add_row(
                    market,
                    f"{pos.amount:.6f}",
                    f"{pos.value:,.2f}",
                    pnl_str,
                )

        table.add_section()
        table.add_row(
            "Total", "", f"[bold]{self._portfolio.total_value:,.2f}[/bold]", ""
        )

        self.update(table)
