"""Trade repository for CRUD operations."""

from __future__ import annotations

import json

from ..models.order import OrderSide
from ..models.trade import Trade
from .database import Database


class TradeRepository:
    def __init__(self, database: Database) -> None:
        self._db = database

    async def insert(self, trade: Trade) -> None:
        await self._db.db.execute(
            """INSERT OR REPLACE INTO trades
               (trade_id, market, side, amount, price, fee, timestamp, strategy_name, pnl, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trade.trade_id,
                trade.market,
                trade.side.value,
                trade.amount,
                trade.price,
                trade.fee,
                trade.timestamp,
                trade.strategy_name,
                trade.pnl,
                json.dumps(trade.metadata),
            ),
        )
        await self._db.db.commit()

    async def get_all(self, market: str | None = None, limit: int = 100) -> list[Trade]:
        if market:
            cursor = await self._db.db.execute(
                "SELECT * FROM trades WHERE market = ? ORDER BY timestamp DESC LIMIT ?",
                (market, limit),
            )
        else:
            cursor = await self._db.db.execute(
                "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
        rows = await cursor.fetchall()
        return [self._row_to_trade(row) for row in rows]

    async def get_by_id(self, trade_id: str) -> Trade | None:
        cursor = await self._db.db.execute(
            "SELECT * FROM trades WHERE trade_id = ?", (trade_id,)
        )
        row = await cursor.fetchone()
        return self._row_to_trade(row) if row else None

    async def count(self, market: str | None = None) -> int:
        if market:
            cursor = await self._db.db.execute(
                "SELECT COUNT(*) FROM trades WHERE market = ?", (market,)
            )
        else:
            cursor = await self._db.db.execute("SELECT COUNT(*) FROM trades")
        row = await cursor.fetchone()
        return row[0] if row else 0

    def _row_to_trade(self, row) -> Trade:
        return Trade(
            trade_id=row["trade_id"],
            market=row["market"],
            side=OrderSide(row["side"]),
            amount=row["amount"],
            price=row["price"],
            fee=row["fee"],
            timestamp=row["timestamp"],
            strategy_name=row["strategy_name"],
            pnl=row["pnl"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
