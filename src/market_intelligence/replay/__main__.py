import argparse
from pathlib import Path

from .engine import replay_snapshots
from .jsonl import load_snapshot_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay normalized market snapshots")
    parser.add_argument("recording", type=Path)
    args = parser.parse_args()

    result = replay_snapshots(load_snapshot_jsonl(args.recording), lambda _: None)
    first = result.first_observed_at.isoformat() if result.first_observed_at else "none"
    last = result.last_observed_at.isoformat() if result.last_observed_at else "none"
    print(f"processed={result.processed} markets={result.market_count} first={first} last={last}")


if __name__ == "__main__":
    main()
