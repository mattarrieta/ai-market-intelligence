# Phase 4 — Replay and Deterministic Anomalies

## Goal

Turn normalized market history into reproducible features and incidents without depending on a live exchange or an AI model.

## Ordered slices

1. Record and replay `MarketSnapshot` JSONL in deterministic event-time order.
2. Calculate rolling price, volume, spread, and liquidity features per market.
3. Apply versioned deterministic anomaly rules.
4. Add cooldown, deduplication, and incident persistence.
5. Verify quiet and anomalous fixtures through end-to-end replay.

## Current status

Steps 1-5 are implemented:

- Strict snapshot validation with stable event-time replay
- Isolated rolling state for every source and ticker
- Midpoint, spread, 30-second and 5-minute price changes
- Non-negative volume deltas, short-window volume, and baseline z-scores
- Five-minute volatility and liquidity decline
- Warm-up protection before incident creation
- Price-shock, volume-spike, spread-anomaly, and liquidity-shock rules
- Deterministic incident identifiers and versioned detector policy
- Per-market, per-detector cooldown suppression
- Stable JSONL incident persistence for audit and comparison
- Quiet, price, volume, and liquidity replay fixtures

Thresholds are provisional defaults. They will be calibrated against observed market distributions before continuous live detection is enabled.

## Run an end-to-end detection replay

```powershell
python -m market_intelligence.replay datasets/recorded-events/price-shock-v1.jsonl --show-features --incidents data/incidents.jsonl
```

The command prints detected incidents and can persist deterministic JSONL output. Repeating it with the same recording and policy produces identical incident content.

## Important boundary

Market selection is upstream configuration. Replay and detection consume normalized snapshots, so changing categories, activity thresholds, or watchlist size does not change their contracts.

AI is also downstream. These rules create trustworthy incidents; a later bounded agent investigates why an incident may have occurred.

## Exit criteria

- [x] The same recording produces byte-for-byte equivalent incidents on repeated runs.
- [x] Out-of-order input is processed in deterministic event-time order.
- [x] Invalid snapshots fail with their exact recording line number.
- [x] Quiet recordings produce no incidents.
- [x] Price, volume, and liquidity fixtures trigger only their intended detector families.
- [x] Repeated detections inside the configured cooldown do not create duplicate incidents.
