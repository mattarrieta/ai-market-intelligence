from datetime import UTC, datetime

import httpx

from market_intelligence.ingestion import KalshiClient, MarketCollector, SnapshotRepository


def test_collector_fetches_and_persists_one_cycle(tmp_path, market_pages) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        page = market_pages[1] if request.url.params.get("cursor") else market_pages[0]
        return httpx.Response(200, json=page, request=request)

    client = KalshiClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url=KalshiClient.BASE_URL)
    )
    repository = SnapshotRepository(tmp_path / "markets.sqlite3")
    repository.initialize()
    now = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)

    result = MarketCollector(client, repository, clock=lambda: now).collect_once()

    assert result.received == 3
    assert result.inserted == 3
    assert result.observed_at == now
    assert repository.count() == 3
