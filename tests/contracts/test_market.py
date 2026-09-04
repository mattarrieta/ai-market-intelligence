from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from market_intelligence.contracts import MarketEvent, MarketEventType

UTC_NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


def make_event(**overrides: object) -> MarketEvent:
    values: dict[str, object] = {
        "event_id": "event-1",
        "source": "kalshi",
        "event_type": MarketEventType.TRADE,
        "ticker": "KXFED-SEP",
        "exchange_timestamp": UTC_NOW,
        "received_timestamp": UTC_NOW,
        "price": Decimal("0.62"),
        "quantity": Decimal("100"),
    }
    values.update(overrides)
    return MarketEvent.model_validate(values)


def test_market_event_accepts_normalized_values() -> None:
    event = make_event()
    assert event.price == Decimal("0.62")
    assert event.schema_version == "1.0"


@pytest.mark.parametrize("price", [Decimal("-0.01"), Decimal("1.01")])
def test_market_event_rejects_invalid_probability(price: Decimal) -> None:
    with pytest.raises(ValidationError):
        make_event(price=price)


def test_market_event_requires_utc() -> None:
    with pytest.raises(ValidationError, match="UTC"):
        make_event(exchange_timestamp=datetime(2026, 9, 3, 12, 0))


def test_market_event_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        make_event(exchange_secret="unexpected")


def test_contracts_are_immutable() -> None:
    event = make_event()
    with pytest.raises(ValidationError):
        event.ticker = "CHANGED"  # type: ignore[misc]
