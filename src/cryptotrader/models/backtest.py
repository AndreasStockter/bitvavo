"""Backtest result data models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .trade import Trade


@dataclass(slots=True)
class BacktestResult:
    strategy_name: str
    params: dict
    initial_capital: float
    final_capital: float
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_return_pct: float = 0.0
    num_trades: int = 0

    def __post_init__(self) -> None:
        if self.initial_capital > 0:
            self.total_return_pct = (
                (self.final_capital - self.initial_capital) / self.initial_capital
            ) * 100


@dataclass(slots=True)
class SweepResult:
    strategy_name: str
    param_grid: dict[str, list]
    results: list[BacktestResult] = field(default_factory=list)

    @property
    def best_result(self) -> BacktestResult | None:
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.sharpe_ratio)
