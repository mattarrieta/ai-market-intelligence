# Phase 1 — Repository and Contracts

## Scope

This phase establishes project standards and versioned contracts. It intentionally does not connect to Kalshi, a database, AWS, or an LLM.

## Included

- Python packaging and development-tool configuration
- Strict, immutable Pydantic boundary contracts
- UTC timestamp and probability validation
- Market event, features, incident, and evidence types
- Agent budgets, hypotheses, claims, usage, and tool traces
- Golden evaluation case expectations
- Architecture decision records
- GitHub Actions lint, format, type-check, and test workflow

## Verification

```powershell
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest
```

Phase 2 will add the golden dataset, deterministic graders, aggregate reports, and the first CI evaluation gate.
