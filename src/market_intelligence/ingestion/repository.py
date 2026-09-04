from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from decimal import Decimal
from pathlib import Path

from market_intelligence.contracts.snapshot import MarketSnapshot


class SnapshotRepository:
    """SQLite persistence adapter for local development and replay."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self._database_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    source TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    event_ticker TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    close_time TEXT,
                    yes_bid TEXT,
                    yes_ask TEXT,
                    last_price TEXT,
                    volume TEXT NOT NULL,
                    volume_24h TEXT NOT NULL,
                    open_interest TEXT NOT NULL,
                    liquidity_dollars TEXT,
                    schema_version TEXT NOT NULL,
                    PRIMARY KEY (source, ticker, observed_at)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshot_ticker_time "
                "ON market_snapshots (ticker, observed_at DESC)"
            )
            connection.commit()

    @staticmethod
    def _decimal(value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    def save_all(self, snapshots: Iterable[MarketSnapshot]) -> int:
        rows = [
            (
                item.source,
                item.ticker,
                item.event_ticker,
                item.title,
                item.status,
                item.observed_at.isoformat(),
                item.close_time.isoformat() if item.close_time else None,
                self._decimal(item.yes_bid),
                self._decimal(item.yes_ask),
                self._decimal(item.last_price),
                str(item.volume),
                str(item.volume_24h),
                str(item.open_interest),
                self._decimal(item.liquidity_dollars),
                item.schema_version,
            )
            for item in snapshots
        ]
        with closing(sqlite3.connect(self._database_path)) as connection:
            before = connection.total_changes
            connection.executemany(
                """
                INSERT OR IGNORE INTO market_snapshots VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            connection.commit()
            return connection.total_changes - before

    def count(self) -> int:
        with closing(sqlite3.connect(self._database_path)) as connection:
            row = connection.execute("SELECT COUNT(*) FROM market_snapshots").fetchone()
        return int(row[0]) if row else 0

    def latest(self, ticker: str) -> MarketSnapshot | None:
        with closing(sqlite3.connect(self._database_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM market_snapshots WHERE ticker = ? ORDER BY observed_at DESC LIMIT 1",
                (ticker,),
            ).fetchone()
        return MarketSnapshot.model_validate(dict(row)) if row else None
