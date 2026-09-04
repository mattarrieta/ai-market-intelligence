from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from market_intelligence.contracts.snapshot import MarketSnapshot
from market_intelligence.ingestion.featured import fetch_featured_market, select_featured_market
from market_intelligence.ingestion.kalshi import KalshiClient, KalshiClientError


def snapshot(ticker: str, volume_24h: str, volume: str = "0") -> MarketSnapshot:
    return MarketSnapshot(
        source="kalshi",
        ticker=ticker,
        event_ticker=f"EVENT-{ticker}",
        title=ticker,
        status="active",
        observed_at=datetime(2026, 9, 3, 15, 0, tzinfo=UTC),
        volume_24h=Decimal(volume_24h),
        volume=Decimal(volume),
    )


def test_select_featured_market_uses_24_hour_volume() -> None:
    featured = select_featured_market(
        [snapshot("LOW", "10", "1000"), snapshot("HIGH", "500", "500")]
    )

    assert featured.ticker == "HIGH"


def test_select_featured_market_rejects_empty_page() -> None:
    with pytest.raises(KalshiClientError, match="no eligible"):
        select_featured_market([])


def test_fetch_featured_market_is_one_page_and_excludes_combos(market_pages) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=market_pages[0], request=request)

    client = KalshiClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url=KalshiClient.BASE_URL)
    )

    featured = fetch_featured_market(client, datetime(2026, 9, 3, 15, 0, tzinfo=UTC), limit=2)

    assert featured.ticker == "KXFED-SEP"
    assert len(requests) == 1
    assert requests[0].url.params["status"] == "open"
    assert requests[0].url.params["limit"] == "2"
    assert requests[0].url.params["mve_filter"] == "exclude"
