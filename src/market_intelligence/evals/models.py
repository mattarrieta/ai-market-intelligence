from decimal import Decimal

from pydantic import Field

from market_intelligence.contracts import ContractModel


class CaseEvaluation(ContractModel):
    case_id: str
    classification_score: Decimal = Field(ge=0, le=1)
    factuality_score: Decimal = Field(ge=0, le=1)
    citation_score: Decimal = Field(ge=0, le=1)
    tool_score: Decimal = Field(ge=0, le=1)
    cost_within_limit: bool
    latency_within_limit: bool
    estimated_cost_usd: Decimal = Field(ge=0)
    latency_ms: int = Field(ge=0)
    failures: tuple[str, ...] = ()

    @property
    def quality_score(self) -> Decimal:
        return (
            Decimal("0.30") * self.classification_score
            + Decimal("0.30") * self.factuality_score
            + Decimal("0.25") * self.citation_score
            + Decimal("0.15") * self.tool_score
        )


class EvaluationSummary(ContractModel):
    dataset_version: str
    case_count: int = Field(ge=1)
    quality_score: Decimal = Field(ge=0, le=1)
    classification_score: Decimal = Field(ge=0, le=1)
    factuality_score: Decimal = Field(ge=0, le=1)
    citation_score: Decimal = Field(ge=0, le=1)
    tool_score: Decimal = Field(ge=0, le=1)
    average_cost_usd: Decimal = Field(ge=0)
    p95_latency_ms: int = Field(ge=0)
    cost_limit_pass_rate: Decimal = Field(ge=0, le=1)
    latency_limit_pass_rate: Decimal = Field(ge=0, le=1)
    cases: tuple[CaseEvaluation, ...]
