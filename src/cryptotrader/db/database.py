"""SQLite database connection via aiosqlite."""

from __future__ import annotations

import aiosqlite


class Database:
    def __init__(self, path: str = "trades.db") -> None:
        self.path = path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self.path)
        self._db.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db

    async def _create_tables(self) -> None:
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                market TEXT NOT NULL,
                side TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                fee REAL NOT NULL DEFAULT 0,
                timestamp INTEGER NOT NULL,
                strategy_name TEXT DEFAULT '',
                pnl REAL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market)
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)
        """)
        await self.db.commit()
