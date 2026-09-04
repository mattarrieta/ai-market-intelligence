from decimal import Decimal

from pydantic import Field

from market_intelligence.contracts import ContractModel

from .models import EvaluationSummary


class QualityGate(ContractModel):
    minimum_quality: Decimal = Field(default=Decimal("0.95"), ge=0, le=1)
    minimum_classification: Decimal = Field(default=Decimal("0.95"), ge=0, le=1)
    minimum_factuality: Decimal = Field(default=Decimal("0.95"), ge=0, le=1)
    minimum_citations: Decimal = Field(default=Decimal("0.95"), ge=0, le=1)
    minimum_tool_score: Decimal = Field(default=Decimal("0.90"), ge=0, le=1)
    minimum_cost_pass_rate: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)
    minimum_latency_pass_rate: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)


class ReleaseGateResult(ContractModel):
    passed: bool
    failures: tuple[str, ...] = ()


def apply_quality_gate(
    summary: EvaluationSummary, gate: QualityGate | None = None
) -> ReleaseGateResult:
    configured = gate or QualityGate()
    checks = (
        ("quality", summary.quality_score, configured.minimum_quality),
        ("classification", summary.classification_score, configured.minimum_classification),
        ("factuality", summary.factuality_score, configured.minimum_factuality),
        ("citations", summary.citation_score, configured.minimum_citations),
        ("tool use", summary.tool_score, configured.minimum_tool_score),
        ("cost limit pass rate", summary.cost_limit_pass_rate, configured.minimum_cost_pass_rate),
        (
            "latency limit pass rate",
            summary.latency_limit_pass_rate,
            configured.minimum_latency_pass_rate,
        ),
    )
    failures = tuple(
        f"{name} {actual:.3f} is below required {minimum:.3f}"
        for name, actual, minimum in checks
        if actual < minimum
    )
    return ReleaseGateResult(passed=not failures, failures=failures)
