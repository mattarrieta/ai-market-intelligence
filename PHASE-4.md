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

Step 1 is implemented with:

- Strict Pydantic validation at the recording boundary
- Stable ordering by observation time, source, and ticker
- A callback-based replay engine that is independent of detector code
- A synthetic price-shock recording
- Offline round-trip, ordering, empty-input, and malformed-input tests

Steps 2-5 remain in progress.

## Run the replay foundation

```powershell
python -m market_intelligence.replay datasets/recorded-events/price-shock-v1.jsonl
```

## Important boundary

Market selection is upstream configuration. Replay consumes normalized snapshots, so changing categories, activity thresholds, or watchlist size does not change replay or detector contracts.

## Exit criteria

- The same recording produces byte-for-byte equivalent incidents on repeated runs.
- Out-of-order input is processed in deterministic event-time order.
- Invalid snapshots fail with their exact recording line number.
- Quiet recordings produce no incidents.
- Price, volume, and liquidity fixtures trigger only their intended detector families.
- Repeated detections inside the configured cooldown do not create duplicate incidents.
