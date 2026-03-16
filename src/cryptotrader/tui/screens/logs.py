"""Log screen - scrolling log view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog


class LogScreen(Screen):
    BINDINGS = [
        ("1", "app.switch_mode('dashboard')", "Dashboard"),
        ("2", "app.switch_mode('backtest')", "Backtest"),
        ("3", "app.switch_mode('orders')", "Orders"),
        ("4", "app.switch_mode('logs')", "Logs"),
        ("q", "app.quit", "Quit"),
        ("c", "clear_logs", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="screen-container"):
            yield RichLog(id="log-view", highlight=True, markup=True)
        yield Footer()

    def write_log(self, message: str) -> None:
        log_widget = self.query_one("#log-view", RichLog)
        log_widget.write(message)

    def action_clear_logs(self) -> None:
        log_widget = self.query_one("#log-view", RichLog)
        log_widget.clear()
