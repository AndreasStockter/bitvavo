"""Main Textual application with screen navigation via MODES."""

from __future__ import annotations

import logging
from typing import Any

from textual.app import App

from .api.paper import PaperTradingClient
from .config.loader import load_config
from .config.schema import AppConfig
from .db.database import Database
from .db.repository import TradeRepository
from .engine.loop import TradingLoop
from .engine.trading import TradingEngine
from .notifications.telegram import NullNotifier, TelegramNotifier
from .risk.manager import RiskManager
from .strategies import BollingerBands, CompositeStrategy, MACrossover, RSIStrategy
from .strategies.rsi import MultiTimeframeRSIStrategy
from .strategies.base import Strategy
from .tui.screens.backtest import BacktestScreen
from .tui.screens.dashboard import DashboardScreen
from .tui.screens.logs import LogScreen
from .tui.screens.orders import OrdersScreen
from .tui.screens.settings import SettingsScreen

logger = logging.getLogger(__name__)

def build_strategy(config: AppConfig) -> Strategy:
    """Build strategy based on config."""
    name = config.strategy.name

    if name == "ma_crossover":
        return MACrossover(
            fast_period=config.strategy.ma_crossover.fast_period,
            slow_period=config.strategy.ma_crossover.slow_period,
        )
    elif name == "rsi":
        rsi_cfg = config.strategy.rsi
        if rsi_cfg.timeframes:
            timeframes = [
                (tf.interval, RSIStrategy(tf.period, tf.overbought, tf.oversold))
                for tf in rsi_cfg.timeframes
            ]
            return MultiTimeframeRSIStrategy(timeframes, confirmation=rsi_cfg.confirmation)
        return RSIStrategy(
            period=rsi_cfg.period,
            overbought=rsi_cfg.overbought,
            oversold=rsi_cfg.oversold,
        )
    elif name == "bollinger":
        return BollingerBands(
            period=config.strategy.bollinger.period,
            std_dev=config.strategy.bollinger.std_dev,
        )
    elif name == "composite":
        strategies = []
        for s_name in config.strategy.composite.strategies:
            sub_config = AppConfig(**config.model_dump())
            sub_config.strategy.name = s_name
            strategies.append(build_strategy(sub_config))
        return CompositeStrategy(
            strategies=strategies, mode=config.strategy.composite.mode
        )
    else:
        raise ValueError(f"Unknown strategy: {name}")


class CryptoTraderApp(App):
    """Main TUI application for crypto trading."""

    TITLE = "CryptoTrader"
    SUB_TITLE = "Bitvavo Automated Trading"
    CSS_PATH = "tui/styles/app.tcss"

    MODES = {
        "dashboard": DashboardScreen,
        "backtest": BacktestScreen,
        "orders": OrdersScreen,
        "logs": LogScreen,
        "settings": SettingsScreen,
    }

    def __init__(
        self,
        config: AppConfig | None = None,
        config_path: str = "config.yaml",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config or load_config()
        self._config_path = config_path
        self.client: Any = None
        self.strategy: Strategy | None = None
        self.risk_manager: RiskManager | None = None
        self.engine: TradingEngine | None = None
        self.loop: TradingLoop | None = None
        self.database: Database | None = None
        self.repository: TradeRepository | None = None
        self._cached_candles: list = []

    async def on_mount(self) -> None:
        """Initialize all components and switch to dashboard."""
        await self._setup_components()
        self.switch_mode("dashboard")

    async def _setup_components(self) -> None:
        """Set up trading components."""
        # Database
        self.database = Database(self.config.database.path)
        await self.database.connect()
        self.repository = TradeRepository(self.database)

        # API client
        if self.config.trading.mode == "live":
            from .api.client import AsyncBitvavoClient
            self.client = AsyncBitvavoClient(
                api_key=self.config.secrets.bitvavo_api_key,
                api_secret=self.config.secrets.bitvavo_api_secret,
            )
        else:
            self.client = PaperTradingClient(
                initial_balance=self.config.backtest.initial_capital,
                fee_pct=self.config.backtest.fee_pct,
            )

        # Notifier
        if (
            self.config.telegram.enabled
            and self.config.secrets.telegram_bot_token
            and self.config.telegram.chat_id
        ):
            notifier = TelegramNotifier(
                bot_token=self.config.secrets.telegram_bot_token,
                chat_id=self.config.telegram.chat_id,
            )
        else:
            notifier = NullNotifier()

        # Strategy & Engine
        self.strategy = build_strategy(self.config)
        self.risk_manager = RiskManager(self.config.risk)
        self.engine = TradingEngine(
            config=self.config,
            client=self.client,
            strategy=self.strategy,
            risk_manager=self.risk_manager,
            repository=self.repository,
            notifier=notifier,
        )
        self.engine.add_callback(self._on_engine_event)

        # Trading loop
        self.loop = TradingLoop(
            engine=self.engine, interval=self.config.trading.interval
        )

        # Initialize portfolio balance and fetch initial data
        await self.engine.initialize()

        self._log(f"Initialized in {self.config.trading.mode} mode")
        self._log(f"Market: {self.config.trading.market}")
        self._log(f"Strategy: {self.strategy.name}")

    async def _on_engine_event(self, event: str, data: Any) -> None:
        """Handle events from the trading engine."""
        screen = self.screen if isinstance(self.screen, DashboardScreen) else None

        if event == "price_update":
            if screen:
                screen.update_price(data["market"], data["price"])
                screen.query_one("#portfolio-summary").update_portfolio(data["portfolio"])
                if data.get("candles"):
                    self._cached_candles = data["candles"]
                    screen.update_prices_history([c.close for c in self._cached_candles])

        elif event == "initialized":
            if screen:
                screen.query_one("#portfolio-summary").update_portfolio(data)
                screen.query_one("#strategy-panel").set_strategy(self.strategy.name)

        elif event == "signal":
            if screen:
                screen.query_one("#strategy-panel").update_signal(data)
            self._log(f"Signal: {data.signal_type.value} from {data.strategy_name}")

        elif event == "trade":
            self._log(
                f"Trade: {data.side.value.upper()} {data.amount:.6f} @ {data.price:.2f}"
            )

        elif event == "risk_blocked":
            self._log(f"Risk blocked: {data.reason}")

    def _log(self, message: str) -> None:
        """Write a message to the log screen."""
        try:
            log_screen = self.get_screen("logs")
            if isinstance(log_screen, LogScreen):
                log_screen.write_log(message)
        except Exception:
            logger.info(message)

    def toggle_trading(self) -> None:
        """Start or stop the trading loop."""
        if self.loop is None:
            return

        async def _toggle() -> None:
            if self.loop.is_running:
                await self.loop.stop()
                self._log("Trading stopped")
            else:
                await self.loop.start()
                self._log("Trading started")
            if isinstance(self.screen, DashboardScreen):
                self.screen.update_trading_status(self.loop.is_running)

        self.run_worker(_toggle())

    async def apply_new_config(self, new_config: AppConfig) -> None:
        """Apply updated config without restarting the app."""
        was_running = self.loop is not None and self.loop.is_running
        if was_running:
            await self.loop.stop()

        self.config = new_config
        self.strategy = build_strategy(new_config)
        self.risk_manager = RiskManager(new_config.risk)

        if new_config.trading.mode == "live" and new_config.secrets.bitvavo_api_key:
            from .api.client import AsyncBitvavoClient
            self.client = AsyncBitvavoClient(
                api_key=new_config.secrets.bitvavo_api_key,
                api_secret=new_config.secrets.bitvavo_api_secret,
            )
        else:
            self.client = PaperTradingClient(
                initial_balance=new_config.backtest.initial_capital,
                fee_pct=new_config.backtest.fee_pct,
            )

        if (
            new_config.telegram.enabled
            and new_config.secrets.telegram_bot_token
            and new_config.telegram.chat_id
        ):
            notifier = TelegramNotifier(
                bot_token=new_config.secrets.telegram_bot_token,
                chat_id=new_config.telegram.chat_id,
            )
        else:
            notifier = NullNotifier()

        self.engine = TradingEngine(
            config=new_config,
            client=self.client,
            strategy=self.strategy,
            risk_manager=self.risk_manager,
            repository=self.repository,
            notifier=notifier,
        )
        self.engine.add_callback(self._on_engine_event)
        self.loop = TradingLoop(engine=self.engine, interval=new_config.trading.interval)

        await self.engine.initialize()
        self._log(f"Config applied — strategy: {self.strategy.name}, mode: {new_config.trading.mode}")

        if was_running:
            await self.loop.start()

    async def action_quit(self) -> None:
        """Clean shutdown."""
        if self.loop and self.loop.is_running:
            await self.loop.stop()
        if self.database:
            await self.database.close()
        self.exit()
