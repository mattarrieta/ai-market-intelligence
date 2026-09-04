from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from market_intelligence.contracts.snapshot import MarketSnapshot

MarketStatus = Literal["unopened", "open", "paused", "closed", "settled"]
MveFilter = Literal["only", "exclude"]
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class KalshiClientError(RuntimeError):
    """Raised when Kalshi data cannot be retrieved or validated."""


class KalshiMarketPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ticker: str = Field(min_length=1)
    event_ticker: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = Field(min_length=1)
    close_time: datetime | None = None
    yes_bid_dollars: Decimal | None = Field(default=None, ge=0, le=1)
    yes_ask_dollars: Decimal | None = Field(default=None, ge=0, le=1)
    last_price_dollars: Decimal | None = Field(default=None, ge=0, le=1)
    volume_fp: Decimal = Field(default=Decimal(0), ge=0)
    volume_24h_fp: Decimal = Field(default=Decimal(0), ge=0)
    open_interest_fp: Decimal = Field(default=Decimal(0), ge=0)
    liquidity_dollars: Decimal | None = Field(default=None, ge=0)


class KalshiMarketsPage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    markets: list[KalshiMarketPayload]
    cursor: str = ""


def normalize_market(payload: KalshiMarketPayload, observed_at: datetime) -> MarketSnapshot:
    """Translate a Kalshi payload into the platform-owned snapshot schema."""

    return MarketSnapshot(
        source="kalshi",
        ticker=payload.ticker,
        event_ticker=payload.event_ticker,
        title=payload.title,
        status=payload.status,
        observed_at=observed_at,
        close_time=payload.close_time,
        yes_bid=payload.yes_bid_dollars,
        yes_ask=payload.yes_ask_dollars,
        last_price=payload.last_price_dollars,
        volume=payload.volume_fp,
        volume_24h=payload.volume_24h_fp,
        open_interest=payload.open_interest_fp,
        liquidity_dollars=payload.liquidity_dollars,
    )


class KalshiClient:
    BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        self._client = client or httpx.Client(base_url=self.BASE_URL, timeout=10.0)
        self._owns_client = client is None
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> KalshiClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _get(self, path: str, params: dict[str, Any]) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self._max_attempts):
            try:
                response = self._client.get(path, params=params)
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                    return response
                last_error = httpx.HTTPStatusError(
                    "retryable Kalshi response",
                    request=response.request,
                    response=response,
                )
            except httpx.RequestError as error:
                last_error = error

            if attempt + 1 < self._max_attempts:
                self._sleep(self._backoff_seconds * (2**attempt))

        raise KalshiClientError(
            f"Kalshi request failed after {self._max_attempts} attempts"
        ) from last_error

    def iter_market_payloads(
        self,
        *,
        status: MarketStatus = "open",
        limit: int = 1000,
        max_pages: int | None = None,
        mve_filter: MveFilter | None = None,
    ) -> Iterator[KalshiMarketPayload]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        if max_pages is not None and max_pages < 1:
            raise ValueError("max_pages must be at least one")

        cursor = ""
        pages_received = 0
        seen_cursors: set[str] = set()
        while True:
            params: dict[str, Any] = {"status": status, "limit": limit}
            if mve_filter is not None:
                params["mve_filter"] = mve_filter
            if cursor:
                params["cursor"] = cursor
            response = self._get("/markets", params)
            try:
                page = KalshiMarketsPage.model_validate(response.json())
            except (ValueError, ValidationError) as error:
                raise KalshiClientError("Kalshi returned an invalid markets response") from error

            yield from page.markets
            pages_received += 1
            if not page.cursor or (max_pages is not None and pages_received >= max_pages):
                return
            if page.cursor in seen_cursors:
                raise KalshiClientError("Kalshi returned a repeated pagination cursor")
            seen_cursors.add(page.cursor)
            cursor = page.cursor

    def list_market_snapshots(
        self,
        observed_at: datetime,
        *,
        status: MarketStatus = "open",
        limit: int = 1000,
        max_pages: int | None = None,
        mve_filter: MveFilter | None = None,
    ) -> list[MarketSnapshot]:
        return [
            normalize_market(payload, observed_at)
            for payload in self.iter_market_payloads(
                status=status,
                limit=limit,
                max_pages=max_pages,
                mve_filter=mve_filter,
            )
        ]
