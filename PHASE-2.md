# Phase 2 — Evaluation Platform Foundation

## Scope

This phase adds credential-free evaluation of recorded agent investigations. Live model calls and subjective model-based graders remain deferred.

## Included

- Ten-case, versioned JSONL golden dataset
- Strict dataset validation and duplicate detection
- Deterministic classification, factuality, citation, and tool-use graders
- Per-case cost and latency limits
- Aggregate quality metrics and P95 latency
- Configurable release gate
- CLI evaluation runner with optional JSON artifact output
- Positive and intentionally negative regression tests
- CI release-gate execution

## Run

```powershell
python -m market_intelligence.evals datasets/golden/market-incidents-v1.jsonl
```

## Exit criteria

- All ten valid cases pass.
- Wrong classifications, prohibited claims, invented citations, missing tools, and budget violations fail for their expected reasons.
- CI runs the evaluation release gate without model credentials.
