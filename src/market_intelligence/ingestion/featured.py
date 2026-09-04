from datetime import datetime

from market_intelligence.contracts.snapshot import MarketSnapshot

from .kalshi import KalshiClient, KalshiClientError


def select_featured_market(snapshots: list[MarketSnapshot]) -> MarketSnapshot:
    """Select the most actively traded snapshot with deterministic tie-breakers."""

    if not snapshots:
        raise KalshiClientError("Kalshi returned no eligible open markets")
    return max(
        snapshots,
        key=lambda market: (
            market.volume_24h,
            market.volume,
            market.open_interest,
            market.ticker,
        ),
    )


def fetch_featured_market(
    client: KalshiClient,
    observed_at: datetime,
    *,
    limit: int = 100,
) -> MarketSnapshot:
    """Fetch one bounded page of ordinary open markets and select its most active market."""

    snapshots = client.list_market_snapshots(
        observed_at,
        status="open",
        limit=limit,
        max_pages=1,
        mve_filter="exclude",
    )
    return select_featured_market(snapshots)
