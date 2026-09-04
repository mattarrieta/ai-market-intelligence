from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime

from market_intelligence.contracts.snapshot import MarketSnapshot


@dataclass(frozen=True)
class ReplayResult:
    processed: int
    market_count: int
    first_observed_at: datetime | None
    last_observed_at: datetime | None


def replay_snapshots(
    snapshots: Iterable[MarketSnapshot],
    handler: Callable[[MarketSnapshot], None],
) -> ReplayResult:
    """Deliver snapshots in stable event-time order without wall-clock delays."""

    ordered = sorted(
        snapshots,
        key=lambda item: (item.observed_at, item.source, item.ticker),
    )
    for snapshot in ordered:
        handler(snapshot)

    if not ordered:
        return ReplayResult(
            processed=0,
            market_count=0,
            first_observed_at=None,
            last_observed_at=None,
        )
    return ReplayResult(
        processed=len(ordered),
        market_count=len({(item.source, item.ticker) for item in ordered}),
        first_observed_at=ordered[0].observed_at,
        last_observed_at=ordered[-1].observed_at,
    )
