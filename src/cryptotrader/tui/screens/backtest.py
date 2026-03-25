"""Backtest screen - sweep configuration, heatmap, results table."""

from __future__ import annotations

from functools import partial

from textual import work
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

from ...backtesting.sweep import ParameterSweep
from ...config.loader import load_config, save_config
from ...models.backtest import BacktestResult
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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sorted_results: list[BacktestResult] = []
        self._sweep_strategy: str = ""

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
                with Horizontal():
                    yield Button("Run Sweep", id="run-sweep", variant="primary")
                    yield Button("Übernehmen", id="apply-params", variant="success", disabled=True)
                yield Static("", id="sweep-status")
            with Vertical(id="backtest-results"):
                yield HeatmapWidget(id="heatmap")
                yield DataTable(id="results-table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#results-table", DataTable)
        table.add_columns("Params", "Return %", "Sharpe", "Max DD", "Win Rate", "Trades")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-sweep":
            await self._fetch_candles_then_sweep()
        elif event.button.id == "apply-params":
            self._apply_selected_params()

    async def _fetch_candles_then_sweep(self) -> None:
        """Fetch candles on the main thread, then run sweep in worker thread."""
        status = self.query_one("#sweep-status", Static)

        select = self.query_one("#strategy-select", Select)
        strategy_name = str(select.value)
        strategy_cls = STRATEGY_MAP.get(strategy_name)
        if not strategy_cls:
            status.update(f"Unknown strategy: {strategy_name}")
            return

        app = self.app
        candles: list[Candle] = getattr(app, "_cached_candles", [])

        if not candles:
            client = getattr(app, "client", None)
            if client:
                config = getattr(app, "config", None)
                market = config.trading.market if config else "BTC-EUR"
                interval = config.trading.interval if config else "1h"
                status.update(f"Lade Candles für {market} ({interval})...")
                try:
                    candles = await client.get_candles(market, interval, limit=500)
                    app._cached_candles = candles  # type: ignore[attr-defined]
                except Exception as e:
                    status.update(f"Fehler beim Laden der Candles: {e}")
                    return

        if len(candles) < 50:
            status.update(
                f"Zu wenig Candle-Daten ({len(candles)} vorhanden, min. 50 nötig)"
            )
            return

        self._do_sweep(strategy_name, strategy_cls, candles)

    @work(thread=True)
    def _do_sweep(self, strategy_name: str, strategy_cls, candles: list[Candle]) -> None:
        """Run the sweep in a background thread."""
        status = self.query_one("#sweep-status", Static)

        config = getattr(self.app, "config", None)
        initial_capital = config.backtest.initial_capital if config else 10000.0
        fee_pct = config.backtest.fee_pct if config else 0.0025

        sweep = ParameterSweep(
            initial_capital=initial_capital,
            fee_pct=fee_pct,
            max_workers=2,
            use_threads=True,
        )

        self.app.call_from_thread(
            status.update, f"Sweep läuft ({strategy_name}, {len(candles)} Candles)..."
        )
        try:
            result = sweep.sweep(strategy_cls, candles)
        except Exception as e:
            self.app.call_from_thread(status.update, f"Sweep-Fehler: {e}")
            return

        # Update heatmap
        heatmap = self.query_one("#heatmap", HeatmapWidget)
        self.app.call_from_thread(heatmap.update_results, result)

        # Update results table
        table = self.query_one("#results-table", DataTable)
        sorted_results = sorted(result.results, key=lambda r: r.sharpe_ratio, reverse=True)
        self._sorted_results = sorted_results[:20]
        self._sweep_strategy = strategy_name

        def _update_table():
            table.clear()
            for r in self._sorted_results:
                params_str = ", ".join(f"{k}={v}" for k, v in r.params.items())
                table.add_row(
                    params_str,
                    f"{r.total_return_pct:.1f}%",
                    f"{r.sharpe_ratio:.3f}",
                    f"{r.max_drawdown:.1%}",
                    f"{r.win_rate:.1%}",
                    str(r.num_trades),
                )
            self.query_one("#apply-params", Button).disabled = False

        self.app.call_from_thread(_update_table)

        best = result.best_result
        if best:
            self.app.call_from_thread(
                status.update,
                f"Done! Best Sharpe: {best.sharpe_ratio:.3f} | "
                f"Return: {best.total_return_pct:.1f}% | "
                f"Params: {best.params}",
            )
        else:
            self.app.call_from_thread(status.update, "Sweep complete, no results.")

    def _apply_selected_params(self) -> None:
        """Apply parameters from the selected row to the config."""
        status = self.query_one("#sweep-status", Static)

        if not self._sorted_results:
            status.update("Keine Ergebnisse vorhanden.")
            return

        table = self.query_one("#results-table", DataTable)
        cursor_row = table.cursor_row
        if cursor_row < 0 or cursor_row >= len(self._sorted_results):
            status.update("Bitte eine Zeile auswählen.")
            return

        selected = self._sorted_results[cursor_row]
        params = selected.params

        # Update the strategy-specific config section
        config = self.app.config  # type: ignore[attr-defined]
        config_dict = config.model_dump()
        config_dict.pop("secrets", None)

        strategy_key = self._sweep_strategy
        if strategy_key in config_dict.get("strategy", {}):
            config_dict["strategy"][strategy_key].update(params)

        config_path = self.app._config_path  # type: ignore[attr-defined]
        save_config(config_dict, config_path)

        new_config = load_config(config_path)
        self.app.run_worker(
            self.app.apply_new_config(new_config)  # type: ignore[attr-defined]
        )

        params_str = ", ".join(f"{k}={v}" for k, v in params.items())
        status.update(
            f"[green]Übernommen: {params_str} "
            f"(Sharpe: {selected.sharpe_ratio:.3f})[/green]"
        )
