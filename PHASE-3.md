# Phase 3 — Public Kalshi REST Collector

## Scope

This phase collects public market snapshots without authentication. WebSockets, order-book reconstruction, anomaly detection, Kafka, and AWS remain deferred.

## Included

- Exchange-independent `MarketSnapshot` contract
- Public Kalshi `/markets` client
- Featured-market selection by highest 24-hour volume on one bounded, non-combo page
- Cursor pagination with repeated-cursor protection
- Exponential retry for network errors, rate limits, and server errors
- Strict normalization of fixed-point prices, volume, open interest, and liquidity
- SQLite historical snapshot repository
- One-cycle collector service and CLI
- Recorded API fixtures and fully offline tests

## Run a live collection

```powershell
python -m market_intelligence.ingestion --database data/markets.sqlite3 --limit 100 --max-pages 1
```

This command uses Kalshi's unauthenticated production market-data API and stores one bounded page of open, non-combo markets.

## Print one featured market

```powershell
python -m market_intelligence.ingestion --featured --limit 100
```

This makes one public request, excludes multivariate combo markets, and prints the market with the highest reported 24-hour volume on that page. It does not write to SQLite.

## Exit criteria

- Pagination and retry behavior are covered by offline tests.
- Raw Kalshi payloads do not escape the ingestion adapter.
- Repeated observations are idempotent by source, ticker, and timestamp.
- Historical values round-trip through SQLite without float conversion.
- The existing evaluation release gate remains green.
