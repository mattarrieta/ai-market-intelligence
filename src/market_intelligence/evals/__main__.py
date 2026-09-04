import argparse
from pathlib import Path

from .dataset import load_jsonl
from .gate import apply_quality_gate
from .runner import evaluate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic agent evaluations")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    summary = evaluate_dataset(load_jsonl(args.dataset))
    gate = apply_quality_gate(summary)

    print(f"dataset={summary.dataset_version} cases={summary.case_count}")
    print(
        f"quality={summary.quality_score:.3f} factuality={summary.factuality_score:.3f} "
        f"citations={summary.citation_score:.3f} tools={summary.tool_score:.3f}"
    )
    print(
        f"average_cost_usd={summary.average_cost_usd:.4f} p95_latency_ms={summary.p95_latency_ms}"
    )

    for case in summary.cases:
        for failure in case.failures:
            print(f"CASE_FAIL {case.case_id}: {failure}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(summary.model_dump_json(indent=2), encoding="utf-8")

    if not gate.passed:
        for failure in gate.failures:
            print(f"GATE_FAIL {failure}")
        raise SystemExit(1)
    print("Release gate passed")


if __name__ == "__main__":
    main()
