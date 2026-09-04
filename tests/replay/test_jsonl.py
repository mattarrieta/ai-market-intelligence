from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from market_intelligence.contracts.snapshot import MarketSnapshot
from market_intelligence.replay import ReplayDataError, load_snapshot_jsonl, write_snapshot_jsonl


def snapshot(observed_at: datetime, ticker: str = "DEMO") -> MarketSnapshot:
    return MarketSnapshot(
        source="synthetic",
        ticker=ticker,
        event_ticker="EVENT",
        title="Demo market",
        status="open",
        observed_at=observed_at,
        yes_bid=Decimal("0.49"),
        yes_ask=Decimal("0.51"),
        last_price=Decimal("0.50"),
    )


def test_jsonl_round_trip_is_ordered(tmp_path: Path) -> None:
    first = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)
    path = tmp_path / "recording.jsonl"

    count = write_snapshot_jsonl(
        path,
        [snapshot(first + timedelta(minutes=1)), snapshot(first)],
    )
    loaded = load_snapshot_jsonl(path)

    assert count == 2
    assert [item.observed_at for item in loaded] == [first, first + timedelta(minutes=1)]


def test_loader_reports_invalid_line(tmp_path: Path) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text('{"ticker":"missing required fields"}\n', encoding="utf-8")

    with pytest.raises(ReplayDataError, match=r"invalid\.jsonl:1"):
        load_snapshot_jsonl(path)
