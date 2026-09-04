from decimal import Decimal

from market_intelligence.contracts import EvaluationCase

from .graders import evaluate_case
from .models import CaseEvaluation, EvaluationSummary


class MissingRecordedOutputError(ValueError):
    """Raised when deterministic evaluation lacks a recorded agent output."""


def _average(values: list[Decimal]) -> Decimal:
    return sum(values, start=Decimal(0)) / Decimal(len(values))


def _p95(values: list[int]) -> int:
    ordered = sorted(values)
    rank = max(1, (95 * len(ordered) + 99) // 100)
    return ordered[rank - 1]


def evaluate_dataset(cases: list[EvaluationCase]) -> EvaluationSummary:
    if not cases:
        raise ValueError("at least one evaluation case is required")

    results: list[CaseEvaluation] = []
    for case in cases:
        if case.recorded_output is None:
            raise MissingRecordedOutputError(f"case has no recorded_output: {case.case_id}")
        results.append(evaluate_case(case, case.recorded_output))

    dataset_versions = {case.dataset_version for case in cases}
    if len(dataset_versions) != 1:
        raise ValueError("all cases must use the same dataset_version")

    return EvaluationSummary(
        dataset_version=dataset_versions.pop(),
        case_count=len(results),
        quality_score=_average([result.quality_score for result in results]),
        classification_score=_average([result.classification_score for result in results]),
        factuality_score=_average([result.factuality_score for result in results]),
        citation_score=_average([result.citation_score for result in results]),
        tool_score=_average([result.tool_score for result in results]),
        average_cost_usd=_average([result.estimated_cost_usd for result in results]),
        p95_latency_ms=_p95([result.latency_ms for result in results]),
        cost_limit_pass_rate=_average(
            [Decimal(int(result.cost_within_limit)) for result in results]
        ),
        latency_limit_pass_rate=_average(
            [Decimal(int(result.latency_within_limit)) for result in results]
        ),
        cases=tuple(results),
    )
