"""Backtesting engine."""

from __future__ import annotations

from ..models.backtest import BacktestResult
from ..models.candle import Candle
from ..models.order import OrderSide
from ..models.portfolio import Portfolio
from ..models.trade import Trade
from ..strategies.base import Strategy
from .metrics import calculate_max_drawdown, calculate_sharpe_ratio, calculate_win_rate


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 10000.0,
        fee_pct: float = 0.0025,
    ) -> None:
        self.initial_capital = initial_capital
        self.fee_pct = fee_pct

    def run(self, strategy: Strategy, candles: list[Candle]) -> BacktestResult:
        """Run a backtest with the given strategy and candle data."""
        portfolio = Portfolio(cash=self.initial_capital)
        trades: list[Trade] = []
        equity_curve: list[float] = []
        market = "BACKTEST"
        trade_count = 0

        for i in range(1, len(candles)):
            window = candles[: i + 1]
            signal = strategy.evaluate(window)
            price = candles[i].close
            ts = candles[i].timestamp

            if signal.signal_type.value == "buy" and portfolio.cash > 0:
                amount = (portfolio.cash * 0.95) / price  # keep 5% buffer
                fee = amount * price * self.fee_pct
                if amount * price + fee <= portfolio.cash:
                    portfolio.update_position(market, amount, price, fee)
                    trade_count += 1
                    trades.append(
                        Trade(
                            trade_id=f"bt-{trade_count}",
                            market=market,
                            side=OrderSide.BUY,
                            amount=amount,
                            price=price,
                            fee=fee,
                            timestamp=ts,
                            strategy_name=strategy.name,
                        )
                    )

            elif signal.signal_type.value == "sell":
                pos = portfolio.get_position(market)
                if pos.amount > 0:
                    amount = pos.amount
                    fee = amount * price * self.fee_pct
                    pnl = (price - pos.avg_entry_price) * amount - fee
                    portfolio.update_position(market, -amount, price, fee)
                    trade_count += 1
                    trades.append(
                        Trade(
                            trade_id=f"bt-{trade_count}",
                            market=market,
                            side=OrderSide.SELL,
                            amount=amount,
                            price=price,
                            fee=fee,
                            timestamp=ts,
                            strategy_name=strategy.name,
                            pnl=pnl,
                        )
                    )

            # Update position current price for equity calculation
            pos = portfolio.get_position(market)
            pos.current_price = price
            equity_curve.append(portfolio.total_value)

        result = BacktestResult(
            strategy_name=strategy.name,
            params={},
            initial_capital=self.initial_capital,
            final_capital=portfolio.total_value,
            trades=trades,
            equity_curve=equity_curve,
            sharpe_ratio=calculate_sharpe_ratio(equity_curve),
            max_drawdown=calculate_max_drawdown(equity_curve),
            win_rate=calculate_win_rate(trades),
            num_trades=len(trades),
        )
        return result
