from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from market_intelligence.contracts.snapshot import MarketSnapshot


def test_snapshot_rejects_crossed_yes_market() -> None:
    with pytest.raises(ValidationError, match="yes_ask must not be below yes_bid"):
        MarketSnapshot(
            source="kalshi",
            ticker="TEST",
            event_ticker="EVENT",
            title="Test market",
            status="open",
            observed_at=datetime(2026, 9, 3, tzinfo=UTC),
            yes_bid=Decimal("0.70"),
            yes_ask=Decimal("0.60"),
        )
