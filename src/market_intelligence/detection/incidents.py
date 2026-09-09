from collections.abc import Iterable
from pathlib import Path

from market_intelligence.contracts.market import Incident


def write_incident_jsonl(path: Path, incidents: Iterable[Incident]) -> int:
    """Persist incidents in stable order for replay comparison and audit."""

    ordered = sorted(
        incidents,
        key=lambda item: (
            item.detected_at,
            item.ticker,
            item.incident_type.value,
            item.incident_id,
        ),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(f"{incident.model_dump_json(exclude_none=True)}\n" for incident in ordered)
    path.write_text(content, encoding="utf-8")
    return len(ordered)
