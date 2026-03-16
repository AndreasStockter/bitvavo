"""Backtest performance metrics."""

from __future__ import annotations

from ..models.trade import Trade
from ..models.order import OrderSide


def calculate_sharpe_ratio(
    equity_curve: list[float], risk_free_rate: float = 0.0
) -> float:
    """Calculate annualized Sharpe ratio from equity curve."""
    if len(equity_curve) < 2:
        return 0.0

    returns = [
        (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
        for i in range(1, len(equity_curve))
        if equity_curve[i - 1] != 0
    ]

    if not returns:
        return 0.0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_return = variance**0.5

    if std_return == 0:
        return 0.0

    # Annualize assuming hourly data (8760 hours/year)
    annualized_return = mean_return * 8760
    annualized_std = std_return * (8760**0.5)

    return (annualized_return - risk_free_rate) / annualized_std


def calculate_max_drawdown(equity_curve: list[float]) -> float:
    """Calculate maximum drawdown as a fraction."""
    if len(equity_curve) < 2:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0

    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)

    return max_dd


def calculate_win_rate(trades: list[Trade]) -> float:
    """Calculate win rate from completed trade pairs."""
    if not trades:
        return 0.0

    sells = [t for t in trades if t.side == OrderSide.SELL]
    if not sells:
        return 0.0

    winning = sum(1 for t in sells if t.pnl is not None and t.pnl > 0)
    return winning / len(sells)


def calculate_metrics(
    equity_curve: list[float], trades: list[Trade]
) -> dict[str, float]:
    """Calculate all metrics for a backtest result."""
    return {
        "sharpe_ratio": calculate_sharpe_ratio(equity_curve),
        "max_drawdown": calculate_max_drawdown(equity_curve),
        "win_rate": calculate_win_rate(trades),
    }
