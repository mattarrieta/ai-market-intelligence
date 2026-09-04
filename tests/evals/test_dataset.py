import json

import pytest

from market_intelligence.evals.dataset import DatasetError, load_jsonl


def test_golden_dataset_contains_ten_versioned_cases(golden_dataset_path) -> None:
    cases = load_jsonl(golden_dataset_path)
    assert len(cases) == 10
    assert {case.dataset_version for case in cases} == {"market-incidents-v1"}


def test_loader_rejects_duplicate_case_ids(tmp_path, golden_dataset_path) -> None:
    first = golden_dataset_path.read_text(encoding="utf-8").splitlines()[0]
    path = tmp_path / "duplicates.jsonl"
    path.write_text(f"{first}\n{first}\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="duplicate case_id"):
        load_jsonl(path)


def test_loader_reports_invalid_line(tmp_path) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text(json.dumps({"case_id": "incomplete"}), encoding="utf-8")
    with pytest.raises(DatasetError, match="invalid case"):
        load_jsonl(path)
