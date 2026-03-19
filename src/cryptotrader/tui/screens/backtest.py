"""Backtest screen - sweep configuration, heatmap, results table."""

from __future__ import annotations

import asyncio
from functools import partial

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Select,
    Static,
)

from ...backtesting.engine import BacktestEngine
from ...backtesting.sweep import ParameterSweep
from ...models.candle import Candle
from ...strategies import BollingerBands, MACrossover, RSIStrategy
from ..widgets.heatmap import HeatmapWidget

STRATEGY_MAP = {
    "ma_crossover": MACrossover,
    "rsi": RSIStrategy,
    "bollinger": BollingerBands,
}


class BacktestScreen(Screen):
    BINDINGS = [
        ("1", "app.switch_mode('dashboard')", "Dashboard"),
        ("2", "app.switch_mode('backtest')", "Backtest"),
        ("3", "app.switch_mode('orders')", "Orders"),
        ("4", "app.switch_mode('logs')", "Logs"),
        ("5", "app.switch_mode('settings')", "Settings"),
        ("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="screen-container"):
            with Vertical(id="backtest-controls"):
                yield Label("Strategy:")
                yield Select(
                    [(name, name) for name in STRATEGY_MAP],
                    id="strategy-select",
                    value="ma_crossover",
                )
                yield Button("Run Sweep", id="run-sweep", variant="primary")
                yield Static("", id="sweep-status")
            with Vertical(id="backtest-results"):
                yield HeatmapWidget(id="heatmap")
                yield DataTable(id="results-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#results-table", DataTable)
        table.add_columns("Params", "Return %", "Sharpe", "Max DD", "Win Rate", "Trades")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-sweep":
            await self._run_sweep()

    async def _run_sweep(self) -> None:
        status = self.query_one("#sweep-status", Static)
        status.update("Running sweep...")

        select = self.query_one("#strategy-select", Select)
        strategy_name = str(select.value)
        strategy_cls = STRATEGY_MAP.get(strategy_name)
        if not strategy_cls:
            status.update(f"Unknown strategy: {strategy_name}")
            return

        # Get candles from the app
        app = self.app
        candles: list[Candle] = getattr(app, "_cached_candles", [])

        if not candles:
            # Try to fetch candles
            client = getattr(app, "client", None)
            if client:
                config = getattr(app, "config", None)
                market = config.trading.market if config else "BTC-EUR"
                interval = config.trading.interval if config else "1h"
                candles = await client.get_candles(market, interval, limit=500)
                app._cached_candles = candles  # type: ignore[attr-defined]

        if len(candles) < 50:
            status.update("Not enough candle data (need >= 50)")
            return

        config = getattr(app, "config", None)
        initial_capital = config.backtest.initial_capital if config else 10000.0
        fee_pct = config.backtest.fee_pct if config else 0.0025

        sweep = ParameterSweep(
            initial_capital=initial_capital,
            fee_pct=fee_pct,
            max_workers=2,
        )

        # Run in thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, partial(sweep.sweep, strategy_cls, candles)
        )

        # Update heatmap
        heatmap = self.query_one("#heatmap", HeatmapWidget)
        heatmap.update_results(result)

        # Update results table
        table = self.query_one("#results-table", DataTable)
        table.clear()
        sorted_results = sorted(result.results, key=lambda r: r.sharpe_ratio, reverse=True)
        for r in sorted_results[:20]:
            params_str = ", ".join(f"{k}={v}" for k, v in r.params.items())
            table.add_row(
                params_str,
                f"{r.total_return_pct:.1f}%",
                f"{r.sharpe_ratio:.3f}",
                f"{r.max_drawdown:.1%}",
                f"{r.win_rate:.1%}",
                str(r.num_trades),
            )

        best = result.best_result
        if best:
            status.update(
                f"Done! Best Sharpe: {best.sharpe_ratio:.3f} | "
                f"Return: {best.total_return_pct:.1f}% | "
                f"Params: {best.params}"
            )
        else:
            status.update("Sweep complete, no results.")
