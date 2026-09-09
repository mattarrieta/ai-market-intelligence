from pathlib import Path

import pytest

from market_intelligence.contracts.enums import IncidentType
from market_intelligence.detection.incidents import write_incident_jsonl
from market_intelligence.detection.pipeline import detect_snapshots
from market_intelligence.replay import load_snapshot_jsonl


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("quiet-v1.jsonl", ()),
        ("volume-spike-v1.jsonl", (IncidentType.VOLUME_SPIKE,)),
        ("liquidity-shock-v1.jsonl", (IncidentType.LIQUIDITY_SHOCK,)),
    ],
)
def test_recordings_trigger_only_expected_incidents(
    filename: str,
    expected: tuple[IncidentType, ...],
) -> None:
    snapshots = load_snapshot_jsonl(Path("datasets/recorded-events") / filename)

    run = detect_snapshots(snapshots)

    assert tuple(incident.incident_type for incident in run.incidents) == expected
    assert run.replay.processed == 6


def test_incident_output_is_byte_for_byte_reproducible(tmp_path: Path) -> None:
    snapshots = load_snapshot_jsonl(Path("datasets/recorded-events/volume-spike-v1.jsonl"))
    first_run = detect_snapshots(snapshots)
    second_run = detect_snapshots(snapshots)
    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"

    assert write_incident_jsonl(first_path, first_run.incidents) == 1
    assert write_incident_jsonl(second_path, second_run.incidents) == 1
    assert first_path.read_bytes() == second_path.read_bytes()


def test_price_fixture_emits_price_shock_after_fixture_isolated() -> None:
    snapshots = load_snapshot_jsonl(Path("datasets/recorded-events/price-shock-v1.jsonl"))
    run = detect_snapshots(snapshots)

    assert tuple(incident.incident_type for incident in run.incidents) == (
        IncidentType.PRICE_SHOCK,
    )
