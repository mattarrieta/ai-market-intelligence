from copy import deepcopy

from market_intelligence.contracts import EvaluationCase
from market_intelligence.evals import QualityGate, evaluate_dataset, load_jsonl
from market_intelligence.evals.gate import apply_quality_gate


def test_golden_dataset_passes_release_gate(golden_dataset_path) -> None:
    summary = evaluate_dataset(load_jsonl(golden_dataset_path))
    result = apply_quality_gate(summary)
    assert summary.case_count == 10
    assert result.passed
    assert result.failures == ()


def test_bad_candidate_fails_release_gate(golden_dataset_path) -> None:
    cases = load_jsonl(golden_dataset_path)
    first = cases[0]
    assert first.recorded_output is not None
    bad_output_data = deepcopy(first.recorded_output.model_dump())
    bad_output_data["classification"] = "NEWS_DRIVEN"
    bad_case = EvaluationCase.model_validate(
        {**first.model_dump(), "recorded_output": bad_output_data}
    )
    summary = evaluate_dataset([bad_case, *cases[1:]])
    result = apply_quality_gate(summary, QualityGate(minimum_classification="0.95"))
    assert not result.passed
    assert any("classification" in failure for failure in result.failures)
