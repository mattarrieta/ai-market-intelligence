from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from .common import ContractModel, require_utc


class MarketSnapshot(ContractModel):
    """Exchange-independent point-in-time view of a binary market."""

    schema_version: str = "1.0"
    source: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    event_ticker: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = Field(min_length=1)
    observed_at: datetime
    close_time: datetime | None = None
    yes_bid: Decimal | None = Field(default=None, ge=0, le=1)
    yes_ask: Decimal | None = Field(default=None, ge=0, le=1)
    last_price: Decimal | None = Field(default=None, ge=0, le=1)
    volume: Decimal = Field(default=Decimal(0), ge=0)
    volume_24h: Decimal = Field(default=Decimal(0), ge=0)
    open_interest: Decimal = Field(default=Decimal(0), ge=0)
    liquidity_dollars: Decimal | None = Field(default=None, ge=0)

    _observed_utc = field_validator("observed_at")(require_utc)

    @field_validator("close_time")
    @classmethod
    def close_time_is_utc(cls, value: datetime | None) -> datetime | None:
        return require_utc(value) if value is not None else None

    @model_validator(mode="after")
    def ask_must_not_be_below_bid(self) -> MarketSnapshot:
        if self.yes_bid is not None and self.yes_ask is not None and self.yes_ask < self.yes_bid:
            raise ValueError("yes_ask must not be below yes_bid")
        return self
