import argparse
from pathlib import Path

from market_intelligence.contracts.market import MarketFeatures
from market_intelligence.contracts.snapshot import MarketSnapshot
from market_intelligence.detection import RollingFeatureCalculator

from .engine import replay_snapshots
from .jsonl import load_snapshot_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay normalized market snapshots")
    parser.add_argument("recording", type=Path)
    parser.add_argument(
        "--show-features",
        action="store_true",
        help="print the final rolling features for each market",
    )
    args = parser.parse_args()

    calculator = RollingFeatureCalculator()
    latest: dict[tuple[str, str], MarketFeatures] = {}

    def handle(snapshot: MarketSnapshot) -> None:
        latest[(snapshot.source, snapshot.ticker)] = calculator.calculate(snapshot)

    result = replay_snapshots(load_snapshot_jsonl(args.recording), handle)
    first = result.first_observed_at.isoformat() if result.first_observed_at else "none"
    last = result.last_observed_at.isoformat() if result.last_observed_at else "none"
    print(f"processed={result.processed} markets={result.market_count} first={first} last={last}")
    if args.show_features:
        for key in sorted(latest):
            print(f"features={key[0]}:{key[1]}")
            print(latest[key].model_dump_json(indent=2))


if __name__ == "__main__":
    main()
