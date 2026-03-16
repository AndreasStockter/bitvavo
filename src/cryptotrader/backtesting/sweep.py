"""Parameter sweep for strategy optimization using ProcessPoolExecutor."""

from __future__ import annotations

import itertools
import logging
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from ..models.backtest import BacktestResult, SweepResult
from ..models.candle import Candle
from ..strategies.base import ParameterSpec, Strategy
from .engine import BacktestEngine

logger = logging.getLogger(__name__)


def _run_single_backtest(
    params: dict,
    strategy_cls_name: str,
    candles_data: list[tuple],
    initial_capital: float,
    fee_pct: float,
) -> BacktestResult:
    """Run a single backtest in a subprocess. Reconstructs objects from serializable data."""
    from ..strategies import BollingerBands, MACrossover, RSIStrategy

    strategy_map = {
        "MACrossover": MACrossover,
        "RSIStrategy": RSIStrategy,
        "BollingerBands": BollingerBands,
    }

    candles = [Candle(*c) for c in candles_data]
    cls = strategy_map[strategy_cls_name]
    strategy = cls.from_params(params)

    engine = BacktestEngine(initial_capital=initial_capital, fee_pct=fee_pct)
    result = engine.run(strategy, candles)
    result.params = params
    return result


class ParameterSweep:
    def __init__(
        self,
        initial_capital: float = 10000.0,
        fee_pct: float = 0.0025,
        max_workers: int | None = None,
    ) -> None:
        self.initial_capital = initial_capital
        self.fee_pct = fee_pct
        self.max_workers = max_workers

    def sweep(
        self,
        strategy_cls: type[Strategy],
        candles: list[Candle],
        param_specs: list[ParameterSpec] | None = None,
    ) -> SweepResult:
        """Run parameter sweep across all combinations."""
        if param_specs is None:
            param_specs = strategy_cls.parameter_specs()

        param_names = [spec.name for spec in param_specs]
        param_values = [spec.values() for spec in param_specs]
        param_grid = {spec.name: spec.values() for spec in param_specs}

        combinations = [
            dict(zip(param_names, combo))
            for combo in itertools.product(*param_values)
        ]

        # Serialize candles for subprocess
        candles_data = [
            (c.timestamp, c.open, c.high, c.low, c.close, c.volume) for c in candles
        ]

        cls_name = strategy_cls.__name__
        results: list[BacktestResult] = []

        logger.info(
            "Starting sweep: %d combinations for %s", len(combinations), cls_name
        )

        run_fn = partial(
            _run_single_backtest,
            strategy_cls_name=cls_name,
            candles_data=candles_data,
            initial_capital=self.initial_capital,
            fee_pct=self.fee_pct,
        )

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(run_fn, combinations))

        return SweepResult(
            strategy_name=cls_name,
            param_grid=param_grid,
            results=results,
        )
