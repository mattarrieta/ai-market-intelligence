from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from market_intelligence.contracts.enums import IncidentType
from market_intelligence.contracts.market import MarketFeatures
from market_intelligence.contracts.snapshot import MarketSnapshot
from market_intelligence.detection.detector import AnomalyDetector, DetectorPolicy


def snapshot(observed_at: datetime) -> MarketSnapshot:
    return MarketSnapshot(
        source="synthetic",
        ticker="DEMO",
        event_ticker="EVENT",
        title="Demo market",
        status="open",
        observed_at=observed_at,
    )


def features(observed_at: datetime, *, sample_count: int = 6) -> MarketFeatures:
    return MarketFeatures(
        sample_count=sample_count,
        observed_at=observed_at,
        price_change_5m=Decimal("0.20"),
    )


def test_detector_warms_up_before_emitting() -> None:
    observed_at = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)
    detector = AnomalyDetector()

    assert detector.evaluate(snapshot(observed_at), features(observed_at, sample_count=5)) == ()


def test_detector_emits_deterministic_price_incident() -> None:
    observed_at = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)
    first = AnomalyDetector().evaluate(snapshot(observed_at), features(observed_at))[0]
    second = AnomalyDetector().evaluate(snapshot(observed_at), features(observed_at))[0]

    assert first == second
    assert first.incident_type is IncidentType.PRICE_SHOCK
    assert first.severity == Decimal("10.00")
    assert first.detector_version == "rules-1.0.0"


def test_detector_enforces_cooldown() -> None:
    start = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)
    detector = AnomalyDetector()

    assert len(detector.evaluate(snapshot(start), features(start))) == 1
    shortly_after = start + timedelta(minutes=1)
    assert detector.evaluate(snapshot(shortly_after), features(shortly_after)) == ()
    after_cooldown = start + timedelta(minutes=5)
    assert len(detector.evaluate(snapshot(after_cooldown), features(after_cooldown))) == 1


def test_detector_rejects_mismatched_feature_time() -> None:
    observed_at = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="timestamps must match"):
        AnomalyDetector().evaluate(
            snapshot(observed_at),
            features(observed_at + timedelta(seconds=1)),
        )


def test_detector_policy_rejects_invalid_threshold() -> None:
    with pytest.raises(ValueError, match="price_shock_threshold"):
        DetectorPolicy(price_shock_threshold=Decimal(0))
