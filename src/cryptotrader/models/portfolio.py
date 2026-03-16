"""Portfolio and position data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Position:
    market: str
    amount: float = 0.0
    avg_entry_price: float = 0.0
    current_price: float = 0.0

    @property
    def value(self) -> float:
        return self.amount * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        if self.amount == 0:
            return 0.0
        return self.amount * (self.current_price - self.avg_entry_price)

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_entry_price == 0:
            return 0.0
        return (self.current_price - self.avg_entry_price) / self.avg_entry_price


@dataclass(slots=True)
class Portfolio:
    cash: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)

    @property
    def total_value(self) -> float:
        positions_value = sum(p.value for p in self.positions.values())
        return self.cash + positions_value

    def get_position(self, market: str) -> Position:
        if market not in self.positions:
            self.positions[market] = Position(market=market)
        return self.positions[market]

    def update_position(
        self, market: str, amount_delta: float, price: float, fee: float = 0.0
    ) -> None:
        pos = self.get_position(market)
        if amount_delta > 0:  # buy
            total_cost = pos.amount * pos.avg_entry_price + amount_delta * price
            pos.amount += amount_delta
            pos.avg_entry_price = total_cost / pos.amount if pos.amount > 0 else 0.0
            self.cash -= amount_delta * price + fee
        else:  # sell
            pos.amount += amount_delta  # amount_delta is negative
            self.cash += abs(amount_delta) * price - fee
            if pos.amount <= 1e-10:
                pos.amount = 0.0
                pos.avg_entry_price = 0.0
