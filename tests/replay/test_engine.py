from datetime import UTC, datetime, timedelta
from decimal import Decimal

from market_intelligence.contracts.snapshot import MarketSnapshot
from market_intelligence.replay import replay_snapshots


def snapshot(observed_at: datetime, ticker: str) -> MarketSnapshot:
    return MarketSnapshot(
        source="synthetic",
        ticker=ticker,
        event_ticker="EVENT",
        title="Demo market",
        status="open",
        observed_at=observed_at,
        yes_bid=Decimal("0.49"),
        yes_ask=Decimal("0.51"),
    )


def test_replay_delivers_stable_event_time_order() -> None:
    start = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)
    delivered: list[tuple[datetime, str]] = []
    items = [
        snapshot(start + timedelta(minutes=1), "B"),
        snapshot(start, "A"),
        snapshot(start, "B"),
    ]

    result = replay_snapshots(items, lambda item: delivered.append((item.observed_at, item.ticker)))

    assert delivered == [(start, "A"), (start, "B"), (start + timedelta(minutes=1), "B")]
    assert result.processed == 3
    assert result.market_count == 2
    assert result.first_observed_at == start
    assert result.last_observed_at == start + timedelta(minutes=1)


def test_empty_replay_has_empty_boundaries() -> None:
    result = replay_snapshots([], lambda _: None)

    assert result.processed == 0
    assert result.market_count == 0
    assert result.first_observed_at is None
    assert result.last_observed_at is None
