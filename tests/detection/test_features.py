from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from market_intelligence.contracts.snapshot import MarketSnapshot
from market_intelligence.detection import (
    FeaturePolicy,
    OutOfOrderSnapshotError,
    RollingFeatureCalculator,
)
from market_intelligence.replay import load_snapshot_jsonl


def snapshot(
    observed_at: datetime,
    *,
    ticker: str = "DEMO",
    price: str = "0.50",
    volume: str = "100",
    liquidity: str = "500",
) -> MarketSnapshot:
    midpoint = Decimal(price)
    return MarketSnapshot(
        source="synthetic",
        ticker=ticker,
        event_ticker="EVENT",
        title="Demo market",
        status="open",
        observed_at=observed_at,
        yes_bid=midpoint - Decimal("0.01"),
        yes_ask=midpoint + Decimal("0.01"),
        last_price=midpoint,
        volume=Decimal(volume),
        liquidity_dollars=Decimal(liquidity),
    )


def test_price_shock_fixture_produces_expected_features() -> None:
    path = Path("datasets/recorded-events/price-shock-v1.jsonl")
    calculator = RollingFeatureCalculator()

    features = [calculator.calculate(item) for item in load_snapshot_jsonl(path)][-1]

    assert features.sample_count == 6
    assert features.midpoint == Decimal("0.62")
    assert features.spread == Decimal("0.04")
    assert features.price_change_30s is None
    assert features.price_change_5m == Decimal("0.22")
    assert features.volume_delta == Decimal("120")
    assert features.volume_30s == Decimal("120")
    assert features.volume_zscore == Decimal("110")
    assert features.liquidity_decline == (Decimal("510") - Decimal("300")) / Decimal("510")
    assert features.volatility_5m is not None
    assert features.volatility_5m > Decimal(0)


def test_market_histories_are_isolated() -> None:
    calculator = RollingFeatureCalculator()
    start = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)

    calculator.calculate(snapshot(start, ticker="A", price="0.20"))
    calculator.calculate(snapshot(start, ticker="B", price="0.80"))
    result_a = calculator.calculate(
        snapshot(start + timedelta(seconds=30), ticker="A", price="0.25", volume="110")
    )
    result_b = calculator.calculate(
        snapshot(start + timedelta(seconds=30), ticker="B", price="0.79", volume="101")
    )

    assert result_a.price_change_30s == Decimal("0.05")
    assert result_a.volume_delta == Decimal("10")
    assert result_b.price_change_30s == Decimal("-0.01")
    assert result_b.volume_delta == Decimal("1")


def test_volume_counter_reset_is_not_a_spike() -> None:
    calculator = RollingFeatureCalculator()
    start = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)

    calculator.calculate(snapshot(start, volume="500"))
    features = calculator.calculate(snapshot(start + timedelta(minutes=1), volume="5"))

    assert features.volume_delta == Decimal(0)


def test_non_increasing_market_time_is_rejected() -> None:
    calculator = RollingFeatureCalculator()
    observed_at = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)
    calculator.calculate(snapshot(observed_at))

    with pytest.raises(OutOfOrderSnapshotError, match="snapshot time must increase"):
        calculator.calculate(snapshot(observed_at))


def test_policy_validation() -> None:
    with pytest.raises(ValueError, match="short_window"):
        FeaturePolicy(short_window=timedelta(0))
