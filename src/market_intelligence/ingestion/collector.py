from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from .kalshi import KalshiClient
from .repository import SnapshotRepository


@dataclass(frozen=True)
class CollectionResult:
    observed_at: datetime
    received: int
    inserted: int


class MarketCollector:
    def __init__(
        self,
        client: KalshiClient,
        repository: SnapshotRepository,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._client = client
        self._repository = repository
        self._clock = clock

    def collect_once(self, *, limit: int = 1000, max_pages: int | None = None) -> CollectionResult:
        observed_at = self._clock()
        snapshots = self._client.list_market_snapshots(
            observed_at,
            limit=limit,
            max_pages=max_pages,
            mve_filter="exclude",
        )
        inserted = self._repository.save_all(snapshots)
        return CollectionResult(observed_at, len(snapshots), inserted)
