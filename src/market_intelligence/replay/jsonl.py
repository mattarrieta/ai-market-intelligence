from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from market_intelligence.contracts.snapshot import MarketSnapshot


class ReplayDataError(ValueError):
    """Raised when a recorded replay file contains invalid snapshot data."""


def _sort_key(snapshot: MarketSnapshot) -> tuple[object, str, str]:
    return snapshot.observed_at, snapshot.source, snapshot.ticker


def load_snapshot_jsonl(path: Path) -> list[MarketSnapshot]:
    """Load and deterministically order normalized snapshots from JSONL."""

    snapshots: list[MarketSnapshot] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                snapshots.append(MarketSnapshot.model_validate_json(line))
            except (ValueError, ValidationError) as error:
                raise ReplayDataError(f"invalid market snapshot at {path}:{line_number}") from error
    return sorted(snapshots, key=_sort_key)


def write_snapshot_jsonl(path: Path, snapshots: Iterable[MarketSnapshot]) -> int:
    """Write normalized snapshots in deterministic event-time order."""

    ordered = sorted(snapshots, key=_sort_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(f"{snapshot.model_dump_json(exclude_none=True)}\n" for snapshot in ordered)
    path.write_text(content, encoding="utf-8")
    return len(ordered)
