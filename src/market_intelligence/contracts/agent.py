from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator, model_validator

from .common import ContractModel, require_utc
from .enums import ClaimKind, HypothesisStatus, InvestigationStatus


class InvestigationBudget(ContractModel):
    max_tool_calls: int = Field(default=12, ge=1)
    max_evidence_searches: int = Field(default=3, ge=0)
    max_duration_seconds: int = Field(default=90, ge=1)
    max_input_tokens: int = Field(default=20_000, ge=1)
    max_cost_usd: Decimal = Field(default=Decimal("1.00"), ge=0)


class Hypothesis(ContractModel):
    hypothesis_id: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    status: HypothesisStatus = HypothesisStatus.UNTESTED
    evidence_ids: tuple[str, ...] = ()
    rationale: str | None = None


class ToolCallTrace(ContractModel):
    trace_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    started_at: datetime
    finished_at: datetime
    arguments: dict[str, Any] = Field(default_factory=dict)
    result_evidence_ids: tuple[str, ...] = ()
    succeeded: bool
    error_category: str | None = None
    retry_count: int = Field(default=0, ge=0)

    _started_utc = field_validator("started_at")(require_utc)
    _finished_utc = field_validator("finished_at")(require_utc)

    @model_validator(mode="after")
    def validate_outcome(self) -> ToolCallTrace:
        if self.finished_at < self.started_at:
            raise ValueError("finished_at must not precede started_at")
        if self.succeeded and self.error_category is not None:
            raise ValueError("successful tool call cannot have an error_category")
        return self


class Usage(ContractModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: Decimal = Field(ge=0)
    latency_ms: int = Field(ge=0)
    model_calls: int = Field(ge=0)


class Claim(ContractModel):
    kind: ClaimKind
    text: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def facts_require_evidence(self) -> Claim:
        if self.kind is ClaimKind.FACT and not self.evidence_ids:
            raise ValueError("facts must cite at least one evidence_id")
        return self


class InvestigationReport(ContractModel):
    schema_version: str = "1.0"
    investigation_id: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    status: InvestigationStatus
    classification: str = Field(min_length=1)
    confidence: Decimal = Field(ge=0, le=1)
    summary: str = Field(min_length=1)
    claims: tuple[Claim, ...]
    hypotheses: tuple[Hypothesis, ...]
    unknowns: tuple[str, ...] = ()
    tool_calls: tuple[ToolCallTrace, ...] = ()
    usage: Usage
    agent_version: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    model_provider: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    completed_at: datetime

    _completed_utc = field_validator("completed_at")(require_utc)
