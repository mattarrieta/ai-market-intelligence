import argparse
from pathlib import Path

from market_intelligence.detection import detect_snapshots, write_incident_jsonl

from .jsonl import load_snapshot_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay snapshots and detect anomalies")
    parser.add_argument("recording", type=Path)
    parser.add_argument(
        "--show-features",
        action="store_true",
        help="print the final rolling features for each market",
    )
    parser.add_argument(
        "--incidents",
        type=Path,
        help="write detected incidents to deterministic JSONL",
    )
    args = parser.parse_args()

    run = detect_snapshots(load_snapshot_jsonl(args.recording))
    result = run.replay
    first = result.first_observed_at.isoformat() if result.first_observed_at else "none"
    last = result.last_observed_at.isoformat() if result.last_observed_at else "none"
    print(
        f"processed={result.processed} markets={result.market_count} "
        f"incidents={len(run.incidents)} first={first} last={last}"
    )
    for incident in run.incidents:
        print(
            f"incident={incident.incident_type.value} ticker={incident.ticker} "
            f"severity={incident.severity} id={incident.incident_id}"
        )
    if args.incidents:
        saved = write_incident_jsonl(args.incidents, run.incidents)
        print(f"saved={saved} path={args.incidents}")
    if args.show_features:
        for key in sorted(run.final_features):
            print(f"features={key[0]}:{key[1]}")
            print(run.final_features[key].model_dump_json(indent=2))


if __name__ == "__main__":
    main()
