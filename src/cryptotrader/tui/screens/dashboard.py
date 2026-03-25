"""Dashboard screen - price, portfolio, strategy status."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from ..widgets.portfolio_summary import PortfolioSummaryWidget
from ..widgets.price_chart import PriceChartWidget
from ..widgets.strategy_panel import StrategyPanelWidget


class DashboardScreen(Screen):
    BINDINGS = [
        ("1", "app.switch_mode('dashboard')", "Dashboard"),
        ("2", "app.switch_mode('backtest')", "Backtest"),
        ("3", "app.switch_mode('orders')", "Orders"),
        ("4", "app.switch_mode('logs')", "Logs"),
        ("5", "app.switch_mode('settings')", "Settings"),
        ("q", "app.quit", "Quit"),
        ("space", "toggle_trading", "Start/Stop"),
    ]

    async def on_mount(self) -> None:
        """Trigger initial data fetch once the screen is mounted."""
        engine = getattr(self.app, "engine", None)
        strategy = getattr(self.app, "strategy", None)
        if strategy:
            self.query_one("#strategy-panel").set_strategy(strategy.name)
        if engine:
            self.run_worker(engine.tick())

    DEFAULT_CSS = """
    #trading-status {
        text-align: center;
        height: 1;
        margin: 0 1;
    }
    #trading-status.running {
        color: $success;
    }
    #trading-status.stopped {
        color: $error;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="screen-container"):
            yield Static("", id="price-label")
            yield Static("■ GESTOPPT  –  Space zum Starten", id="trading-status", classes="stopped")
            yield PriceChartWidget(id="price-chart")
            with Horizontal(classes="top-row"):
                yield PortfolioSummaryWidget(id="portfolio-summary")
                yield StrategyPanelWidget(id="strategy-panel")
        yield Footer()

    def update_price(self, market: str, price: float) -> None:
        label = self.query_one("#price-label", Static)
        label.update(f"{market}: {price:,.2f} EUR")

    def update_prices_history(self, prices: list[float]) -> None:
        chart = self.query_one("#price-chart", PriceChartWidget)
        chart.update_prices(prices)

    def update_trading_status(self, running: bool) -> None:
        status = self.query_one("#trading-status", Static)
        if running:
            status.set_classes("running")
            status.update("▶ AKTIV  –  Space zum Stoppen")
        else:
            status.set_classes("stopped")
            status.update("■ GESTOPPT  –  Space zum Starten")

    def action_toggle_trading(self) -> None:
        self.app.toggle_trading()  # type: ignore[attr-defined]
