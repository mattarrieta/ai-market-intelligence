import json
from pathlib import Path

from pydantic import ValidationError

from market_intelligence.contracts import EvaluationCase


class DatasetError(ValueError):
    """Raised when a golden dataset cannot be loaded safely."""


def load_jsonl(path: Path) -> list[EvaluationCase]:
    """Load and validate a non-empty, uniquely keyed JSONL evaluation dataset."""

    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()

    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                case = EvaluationCase.model_validate(json.loads(line))
            except (json.JSONDecodeError, ValidationError) as error:
                raise DatasetError(f"invalid case at {path}:{line_number}: {error}") from error
            if case.case_id in seen_ids:
                raise DatasetError(f"duplicate case_id at {path}:{line_number}: {case.case_id}")
            seen_ids.add(case.case_id)
            cases.append(case)

    if not cases:
        raise DatasetError(f"dataset is empty: {path}")
    return cases
