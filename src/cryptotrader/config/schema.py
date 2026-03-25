"""Pydantic configuration models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class TradingConfig(BaseModel):
    market: str = "BTC-EUR"
    interval: str = "1h"
    mode: str = "paper"
    max_open_orders: int = 3


class MACrossoverConfig(BaseModel):
    fast_period: int = 10
    slow_period: int = 30


class RSITimeframeConfig(BaseModel):
    interval: str = "1h"
    period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0


class RSIConfig(BaseModel):
    period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0
    timeframes: list[RSITimeframeConfig] = Field(default_factory=list)
    confirmation: str = "all"  # "all" or "any"


class BollingerConfig(BaseModel):
    period: int = 20
    std_dev: float = 2.0


class CompositeConfig(BaseModel):
    strategies: list[str] = Field(default_factory=lambda: ["ma_crossover", "rsi"])
    mode: str = "majority"


class StrategyConfig(BaseModel):
    name: str = "ma_crossover"
    ma_crossover: MACrossoverConfig = Field(default_factory=MACrossoverConfig)
    rsi: RSIConfig = Field(default_factory=RSIConfig)
    bollinger: BollingerConfig = Field(default_factory=BollingerConfig)
    composite: CompositeConfig = Field(default_factory=CompositeConfig)


class RiskConfig(BaseModel):
    max_position_pct: float = 0.25
    max_drawdown_pct: float = 0.10
    stop_loss_pct: float = 0.0
    take_profit_pct: float = 0.0
    max_daily_trades: int = 10


class BacktestConfig(BaseModel):
    days: int = 90
    initial_capital: float = 10000.0
    fee_pct: float = 0.0025


class TelegramConfig(BaseModel):
    enabled: bool = False
    chat_id: str = ""


class DatabaseConfig(BaseModel):
    path: str = "trades.db"


class SecretsConfig(BaseSettings):
    bitvavo_api_key: str = ""
    bitvavo_api_secret: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


class AppConfig(BaseModel):
    trading: TradingConfig = Field(default_factory=TradingConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
