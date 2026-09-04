from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field, HttpUrl, field_validator

from .common import ContractModel, require_utc
from .enums import EvidenceKind, IncidentType, MarketEventType, MarketHealth


class MarketEvent(ContractModel):
    schema_version: str = "1.0"
    event_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    event_type: MarketEventType
    ticker: str = Field(min_length=1)
    exchange_timestamp: datetime
    received_timestamp: datetime
    price: Decimal | None = Field(default=None, ge=0, le=1)
    quantity: Decimal | None = Field(default=None, ge=0)
    sequence_number: int | None = Field(default=None, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)

    _exchange_utc = field_validator("exchange_timestamp")(require_utc)
    _received_utc = field_validator("received_timestamp")(require_utc)


class MarketFeatures(ContractModel):
    observed_at: datetime
    midpoint: Decimal | None = Field(default=None, ge=0, le=1)
    spread: Decimal | None = Field(default=None, ge=0, le=1)
    price_change_30s: Decimal | None = Field(default=None, ge=-1, le=1)
    price_change_5m: Decimal | None = Field(default=None, ge=-1, le=1)
    volume_30s: Decimal = Field(default=Decimal(0), ge=0)
    volume_zscore: Decimal | None = None
    volatility_5m: Decimal | None = Field(default=None, ge=0)
    yes_depth: Decimal | None = Field(default=None, ge=0)
    no_depth: Decimal | None = Field(default=None, ge=0)
    book_imbalance: Decimal | None = Field(default=None, ge=-1, le=1)
    depth_decline: Decimal | None = Field(default=None, ge=0, le=1)

    _observed_utc = field_validator("observed_at")(require_utc)


class Incident(ContractModel):
    schema_version: str = "1.0"
    incident_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    incident_type: IncidentType
    detected_at: datetime
    severity: Decimal = Field(ge=0, le=10)
    market_health: MarketHealth
    features: MarketFeatures
    detector_version: str = Field(min_length=1)
    supporting_event_ids: tuple[str, ...] = ()

    _detected_utc = field_validator("detected_at")(require_utc)


class Evidence(ContractModel):
    schema_version: str = "1.0"
    evidence_id: str = Field(min_length=1)
    kind: EvidenceKind
    title: str = Field(min_length=1)
    observed_at: datetime
    content: str = Field(min_length=1)
    source_url: HttpUrl | None = None
    source_timestamp: datetime | None = None

    _observed_utc = field_validator("observed_at")(require_utc)

    @field_validator("source_timestamp")
    @classmethod
    def source_timestamp_is_utc(cls, value: datetime | None) -> datetime | None:
        return require_utc(value) if value is not None else None
