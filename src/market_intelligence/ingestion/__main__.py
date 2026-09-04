import argparse
from datetime import UTC, datetime
from pathlib import Path

from .collector import MarketCollector
from .featured import fetch_featured_market
from .kalshi import KalshiClient
from .repository import SnapshotRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect one public Kalshi market snapshot")
    parser.add_argument("--database", type=Path, default=Path("data/markets.sqlite3"))
    parser.add_argument(
        "--featured",
        action="store_true",
        help="print the highest-volume market from one non-combo page without writing",
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=1)
    args = parser.parse_args()

    with KalshiClient() as client:
        if args.featured:
            market = fetch_featured_market(client, datetime.now(UTC), limit=args.limit)
            print(market.model_dump_json(indent=2))
            return

        repository = SnapshotRepository(args.database)
        repository.initialize()
        result = MarketCollector(client, repository).collect_once(
            limit=args.limit,
            max_pages=args.max_pages,
        )
    print(
        f"observed_at={result.observed_at.isoformat()} "
        f"received={result.received} inserted={result.inserted}"
    )


if __name__ == "__main__":
    main()
