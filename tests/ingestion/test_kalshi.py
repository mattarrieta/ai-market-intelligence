from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from market_intelligence.ingestion.kalshi import KalshiClient, KalshiClientError

OBSERVED_AT = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)


def test_client_paginates_and_normalizes(market_pages) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        page = market_pages[1] if request.url.params.get("cursor") else market_pages[0]
        return httpx.Response(200, json=page)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url=KalshiClient.BASE_URL)
    client = KalshiClient(client=http_client)

    snapshots = client.list_market_snapshots(OBSERVED_AT, limit=2)

    assert [item.ticker for item in snapshots] == ["KXFED-SEP", "KXCPI-OVER3", "KXBTC-150K"]
    assert snapshots[0].yes_bid == Decimal("0.6100")
    assert snapshots[0].volume == Decimal("12450.00")
    assert snapshots[0].observed_at == OBSERVED_AT
    assert requests[0].url.params["status"] == "open"
    assert requests[0].url.params["limit"] == "2"
    assert requests[1].url.params["cursor"] == "next-page"


def test_client_can_stop_after_one_page_and_exclude_combos(market_pages) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=market_pages[0], request=request)

    client = KalshiClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url=KalshiClient.BASE_URL)
    )

    snapshots = client.list_market_snapshots(
        OBSERVED_AT, limit=2, max_pages=1, mve_filter="exclude"
    )

    assert len(snapshots) == 2
    assert len(requests) == 1
    assert requests[0].url.params["mve_filter"] == "exclude"


def test_client_retries_transient_status(market_pages) -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(429, request=request)
        return httpx.Response(200, json=market_pages[1], request=request)

    client = KalshiClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url=KalshiClient.BASE_URL),
        max_attempts=3,
        backoff_seconds=0.25,
        sleep=sleeps.append,
    )

    assert len(client.list_market_snapshots(OBSERVED_AT)) == 1
    assert attempts == 3
    assert sleeps == [0.25, 0.5]


def test_client_stops_after_retry_budget() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, request=request)

    client = KalshiClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url=KalshiClient.BASE_URL),
        max_attempts=2,
        sleep=lambda _: None,
    )

    with pytest.raises(KalshiClientError, match="after 2 attempts"):
        client.list_market_snapshots(OBSERVED_AT)


def test_client_rejects_repeated_cursor(market_pages) -> None:
    page = {**market_pages[0], "cursor": "repeated"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=page, request=request)

    client = KalshiClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url=KalshiClient.BASE_URL)
    )

    with pytest.raises(KalshiClientError, match="repeated pagination cursor"):
        list(client.iter_market_payloads())


@pytest.mark.parametrize("limit", [0, 1001])
def test_client_rejects_invalid_page_size(limit: int) -> None:
    client = KalshiClient(client=httpx.Client(base_url=KalshiClient.BASE_URL))
    with pytest.raises(ValueError, match="between 1 and 1000"):
        list(client.iter_market_payloads(limit=limit))


def test_client_rejects_invalid_max_pages() -> None:
    client = KalshiClient(client=httpx.Client(base_url=KalshiClient.BASE_URL))
    with pytest.raises(ValueError, match="at least one"):
        list(client.iter_market_payloads(max_pages=0))
