from copy import deepcopy
from decimal import Decimal

from market_intelligence.contracts import InvestigationReport
from market_intelligence.evals import evaluate_case, load_jsonl


def test_valid_recorded_output_receives_full_quality(golden_dataset_path) -> None:
    case = load_jsonl(golden_dataset_path)[0]
    assert case.recorded_output is not None
    result = evaluate_case(case, case.recorded_output)
    assert result.quality_score == Decimal(1)
    assert result.failures == ()


def changed_report(case, **changes: object) -> InvestigationReport:
    assert case.recorded_output is not None
    data = deepcopy(case.recorded_output.model_dump())
    data.update(changes)
    return InvestigationReport.model_validate(data)


def test_wrong_classification_is_detected(golden_dataset_path) -> None:
    case = load_jsonl(golden_dataset_path)[0]
    result = evaluate_case(case, changed_report(case, classification="NEWS_DRIVEN"))
    assert result.classification_score == 0
    assert any("unexpected classification" in failure for failure in result.failures)


def test_prohibited_claim_zeroes_factuality(golden_dataset_path) -> None:
    case = load_jsonl(golden_dataset_path)[0]
    result = evaluate_case(
        case,
        changed_report(case, summary="The Federal Reserve announced a rate cut."),
    )
    assert result.factuality_score == 0
    assert any("prohibited claim" in failure for failure in result.failures)


def test_unknown_citation_zeroes_citation_score(golden_dataset_path) -> None:
    case = load_jsonl(golden_dataset_path)[0]
    assert case.recorded_output is not None
    claims = [claim.model_dump() for claim in case.recorded_output.claims]
    claims[0]["evidence_ids"] = ("invented-source",)
    result = evaluate_case(case, changed_report(case, claims=claims))
    assert result.citation_score == 0
    assert any("unknown evidence_id" in failure for failure in result.failures)


def test_missing_tool_and_limits_are_detected(golden_dataset_path) -> None:
    case = load_jsonl(golden_dataset_path)[1]
    assert case.recorded_output is not None
    usage = case.recorded_output.usage.model_copy(
        update={"estimated_cost_usd": Decimal("1.00"), "latency_ms": 50_000}
    )
    result = evaluate_case(case, changed_report(case, tool_calls=(), usage=usage))
    assert result.tool_score == 0
    assert not result.cost_within_limit
    assert not result.latency_within_limit
