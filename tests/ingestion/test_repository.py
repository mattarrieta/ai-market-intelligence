from datetime import UTC, datetime, timedelta
from decimal import Decimal

from market_intelligence.contracts.snapshot import MarketSnapshot
from market_intelligence.ingestion.repository import SnapshotRepository


def snapshot(observed_at: datetime, *, price: str = "0.62") -> MarketSnapshot:
    return MarketSnapshot(
        source="kalshi",
        ticker="KXFED-SEP",
        event_ticker="KXFED",
        title="Will the Federal Reserve cut rates?",
        status="open",
        observed_at=observed_at,
        close_time=datetime(2026, 9, 30, 18, 0, tzinfo=UTC),
        yes_bid=Decimal("0.61"),
        yes_ask=Decimal("0.63"),
        last_price=Decimal(price),
        volume=Decimal("100"),
        volume_24h=Decimal("20"),
        open_interest=Decimal("80"),
        liquidity_dollars=Decimal("500"),
    )


def test_repository_persists_history_and_returns_latest(tmp_path) -> None:
    repository = SnapshotRepository(tmp_path / "markets.sqlite3")
    repository.initialize()
    first_time = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)

    assert repository.save_all([snapshot(first_time)]) == 1
    assert repository.save_all([snapshot(first_time)]) == 0
    assert repository.save_all([snapshot(first_time + timedelta(seconds=30), price="0.68")]) == 1
    assert repository.count() == 2
    assert repository.latest("KXFED-SEP").last_price == Decimal("0.68")


def test_repository_returns_none_for_unknown_ticker(tmp_path) -> None:
    repository = SnapshotRepository(tmp_path / "markets.sqlite3")
    repository.initialize()
    assert repository.latest("UNKNOWN") is None
