"""Settings screen – edit and save all configuration parameters."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Switch

from ...config.loader import load_config, save_config
from ...config.schema import RSITimeframeConfig

INTERVALS = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]
INTERVAL_OPTIONS = [(iv, iv) for iv in INTERVALS]
STRATEGY_OPTIONS = [
    ("MA Crossover", "ma_crossover"),
    ("RSI", "rsi"),
    ("Bollinger Bands", "bollinger"),
    ("Composite", "composite"),
]
MODE_OPTIONS = [("Paper (Simulation)", "paper"), ("Live", "live")]
CONFIRM_OPTIONS = [("Alle einig (all)", "all"), ("Einer reicht (any)", "any")]


def _field(label: str, widget) -> Horizontal:
    return Horizontal(Label(label, classes="field-label"), widget, classes="field-row")


class SettingsScreen(Screen):
    BINDINGS = [
        ("1", "app.switch_mode('dashboard')", "Dashboard"),
        ("2", "app.switch_mode('backtest')", "Backtest"),
        ("3", "app.switch_mode('orders')", "Orders"),
        ("4", "app.switch_mode('logs')", "Logs"),
        ("5", "app.switch_mode('settings')", "Settings"),
        ("q", "app.quit", "Quit"),
        ("s", "save_settings", "Save"),
    ]

    DEFAULT_CSS = """
    SettingsScreen .section-header {
        color: $accent;
        text-style: bold;
        margin: 1 0 0 0;
        padding: 0 1;
    }
    SettingsScreen .sub-header {
        color: $text-muted;
        text-style: italic;
        margin: 1 0 0 1;
    }
    SettingsScreen .field-row {
        height: 3;
        align: left middle;
        margin: 0 1;
    }
    SettingsScreen .field-label {
        width: 22;
        content-align: left middle;
        padding: 0 1;
    }
    SettingsScreen Input {
        width: 20;
    }
    SettingsScreen Select {
        width: 30;
    }
    SettingsScreen #save-btn {
        margin: 2 1;
    }
    SettingsScreen #status-label {
        margin: 0 1;
        color: $success;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(classes="screen-container"):

            yield Label("── Trading ──", classes="section-header")
            yield _field("Market:", Input(id="market"))
            yield _field("Interval:", Select(INTERVAL_OPTIONS, id="interval"))
            yield _field("Mode:", Select(MODE_OPTIONS, id="mode"))

            yield Label("── Strategie ──", classes="section-header")
            yield _field("Strategie:", Select(STRATEGY_OPTIONS, id="strategy-name"))

            yield Label("MA Crossover:", classes="sub-header")
            yield _field("Fast Period:", Input(id="ma-fast"))
            yield _field("Slow Period:", Input(id="ma-slow"))

            yield Label("RSI (Einzel-TF):", classes="sub-header")
            yield _field("Period:", Input(id="rsi-period"))
            yield _field("Overbought:", Input(id="rsi-overbought"))
            yield _field("Oversold:", Input(id="rsi-oversold"))

            yield Label("RSI Multi-Timeframe:", classes="sub-header")
            yield _field("Multi-TF aktivieren:", Switch(id="rsi-multi-tf"))
            yield _field("Bestaetigung:", Select(CONFIRM_OPTIONS, id="rsi-confirmation"))

            yield Label("Timeframe 1:", classes="sub-header")
            yield _field("Interval:", Select(INTERVAL_OPTIONS, id="tf1-interval"))
            yield _field("Period:", Input(id="tf1-period"))
            yield _field("Overbought:", Input(id="tf1-overbought"))
            yield _field("Oversold:", Input(id="tf1-oversold"))

            yield Label("Timeframe 2:", classes="sub-header")
            yield _field("Interval:", Select(INTERVAL_OPTIONS, id="tf2-interval"))
            yield _field("Period:", Input(id="tf2-period"))
            yield _field("Overbought:", Input(id="tf2-overbought"))
            yield _field("Oversold:", Input(id="tf2-oversold"))

            yield Label("Bollinger Bands:", classes="sub-header")
            yield _field("Period:", Input(id="bb-period"))
            yield _field("Std Dev:", Input(id="bb-std-dev"))

            yield Label("── Risikomanagement ──", classes="section-header")
            yield _field("Max Position %:", Input(id="risk-max-pos"))
            yield _field("Stop Loss %:", Input(id="risk-stop-loss"))
            yield _field("Take Profit %:", Input(id="risk-take-profit"))
            yield _field("Max Drawdown %:", Input(id="risk-max-dd"))
            yield _field("Max Trades/Tag:", Input(id="risk-max-trades"))

            yield Button("Speichern & Anwenden  [s]", id="save-btn", variant="primary")
            yield Label("", id="status-label")

        yield Footer()

    def on_mount(self) -> None:
        cfg = self.app.config  # type: ignore[attr-defined]
        t = cfg.trading
        s = cfg.strategy
        r = cfg.risk

        self._set(Input, "market", t.market)
        self._set_select("interval", t.interval)
        self._set_select("mode", t.mode)
        self._set_select("strategy-name", s.name)

        self._set(Input, "ma-fast", str(s.ma_crossover.fast_period))
        self._set(Input, "ma-slow", str(s.ma_crossover.slow_period))

        rsi = s.rsi
        self._set(Input, "rsi-period", str(rsi.period))
        self._set(Input, "rsi-overbought", str(rsi.overbought))
        self._set(Input, "rsi-oversold", str(rsi.oversold))

        multi_tf = bool(rsi.timeframes)
        self.query_one("#rsi-multi-tf", Switch).value = multi_tf
        self._set_select("rsi-confirmation", rsi.confirmation)

        tf1 = rsi.timeframes[0] if len(rsi.timeframes) > 0 else RSITimeframeConfig(interval="1h")
        tf2 = rsi.timeframes[1] if len(rsi.timeframes) > 1 else RSITimeframeConfig(interval="1d", overbought=65.0, oversold=35.0)

        self._set_select("tf1-interval", tf1.interval)
        self._set(Input, "tf1-period", str(tf1.period))
        self._set(Input, "tf1-overbought", str(tf1.overbought))
        self._set(Input, "tf1-oversold", str(tf1.oversold))

        self._set_select("tf2-interval", tf2.interval)
        self._set(Input, "tf2-period", str(tf2.period))
        self._set(Input, "tf2-overbought", str(tf2.overbought))
        self._set(Input, "tf2-oversold", str(tf2.oversold))

        self._set(Input, "bb-period", str(s.bollinger.period))
        self._set(Input, "bb-std-dev", str(s.bollinger.std_dev))

        self._set(Input, "risk-max-pos", str(r.max_position_pct))
        self._set(Input, "risk-stop-loss", str(r.stop_loss_pct))
        self._set(Input, "risk-take-profit", str(r.take_profit_pct))
        self._set(Input, "risk-max-dd", str(r.max_drawdown_pct))
        self._set(Input, "risk-max-trades", str(r.max_daily_trades))

    def _set(self, widget_type, widget_id: str, value: str) -> None:
        self.query_one(f"#{widget_id}", widget_type).value = value

    def _set_select(self, widget_id: str, value: str) -> None:
        self.query_one(f"#{widget_id}", Select).value = value

    def _get(self, widget_id: str) -> str:
        return self.query_one(f"#{widget_id}", Input).value.strip()

    def _get_select(self, widget_id: str) -> str:
        return str(self.query_one(f"#{widget_id}", Select).value)

    def _f(self, widget_id: str) -> float:
        try:
            return float(self._get(widget_id))
        except ValueError:
            return 0.0

    def _i(self, widget_id: str) -> int:
        try:
            return int(self._get(widget_id))
        except ValueError:
            return 0

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            await self.action_save_settings()

    async def action_save_settings(self) -> None:
        multi_tf = self.query_one("#rsi-multi-tf", Switch).value

        if multi_tf:
            rsi_cfg: dict = {
                "period": 14,
                "overbought": 70.0,
                "oversold": 30.0,
                "confirmation": self._get_select("rsi-confirmation"),
                "timeframes": [
                    {
                        "interval": self._get_select("tf1-interval"),
                        "period": self._i("tf1-period"),
                        "overbought": self._f("tf1-overbought"),
                        "oversold": self._f("tf1-oversold"),
                    },
                    {
                        "interval": self._get_select("tf2-interval"),
                        "period": self._i("tf2-period"),
                        "overbought": self._f("tf2-overbought"),
                        "oversold": self._f("tf2-oversold"),
                    },
                ],
            }
        else:
            rsi_cfg = {
                "period": self._i("rsi-period"),
                "overbought": self._f("rsi-overbought"),
                "oversold": self._f("rsi-oversold"),
            }

        config_dict = {
            "trading": {
                "market": self._get("market"),
                "interval": self._get_select("interval"),
                "mode": self._get_select("mode"),
                "max_open_orders": self.app.config.trading.max_open_orders,  # type: ignore[attr-defined]
            },
            "strategy": {
                "name": self._get_select("strategy-name"),
                "ma_crossover": {
                    "fast_period": self._i("ma-fast"),
                    "slow_period": self._i("ma-slow"),
                },
                "rsi": rsi_cfg,
                "bollinger": {
                    "period": self._i("bb-period"),
                    "std_dev": self._f("bb-std-dev"),
                },
                "composite": self.app.config.strategy.composite.model_dump(),  # type: ignore[attr-defined]
            },
            "risk": {
                "max_position_pct": self._f("risk-max-pos"),
                "stop_loss_pct": self._f("risk-stop-loss"),
                "take_profit_pct": self._f("risk-take-profit"),
                "max_drawdown_pct": self._f("risk-max-dd"),
                "max_daily_trades": self._i("risk-max-trades"),
            },
            "backtest": self.app.config.backtest.model_dump(),  # type: ignore[attr-defined]
            "telegram": self.app.config.telegram.model_dump(),  # type: ignore[attr-defined]
            "database": self.app.config.database.model_dump(),  # type: ignore[attr-defined]
        }

        config_path = self.app._config_path  # type: ignore[attr-defined]
        save_config(config_dict, config_path)

        new_config = load_config(config_path)
        await self.app.apply_new_config(new_config)  # type: ignore[attr-defined]

        self.query_one("#status-label", Label).update(
            f"[green]Gespeichert und angewendet ({config_path})[/green]"
        )
