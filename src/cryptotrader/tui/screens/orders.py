"""Orders screen - open orders and trade history."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from ...models.trade import Trade


class OrdersScreen(Screen):
    BINDINGS = [
        ("1", "app.switch_mode('dashboard')", "Dashboard"),
        ("2", "app.switch_mode('backtest')", "Backtest"),
        ("3", "app.switch_mode('orders')", "Orders"),
        ("4", "app.switch_mode('logs')", "Logs"),
        ("5", "app.switch_mode('settings')", "Settings"),
        ("q", "app.quit", "Quit"),
        ("r", "refresh_orders", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="screen-container"):
            yield Static("Trade History", classes="section-title")
            yield DataTable(id="orders-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#orders-table", DataTable)
        table.add_columns(
            "Time", "Market", "Side", "Amount", "Price", "Fee", "PnL", "Strategy"
        )

    def update_trades(self, trades: list[Trade]) -> None:
        table = self.query_one("#orders-table", DataTable)
        table.clear()
        for t in trades:
            from datetime import datetime, timezone

            ts = datetime.fromtimestamp(t.timestamp / 1000, tz=timezone.utc)
            time_str = ts.strftime("%Y-%m-%d %H:%M")
            pnl_str = f"{t.pnl:+.2f}" if t.pnl is not None else "-"
            side_str = t.side.value.upper()
            table.add_row(
                time_str,
                t.market,
                side_str,
                f"{t.amount:.6f}",
                f"{t.price:.2f}",
                f"{t.fee:.4f}",
                pnl_str,
                t.strategy_name,
            )

    async def action_refresh_orders(self) -> None:
        repo = getattr(self.app, "repository", None)
        if repo:
            trades = await repo.get_all(limit=50)
            self.update_trades(trades)
