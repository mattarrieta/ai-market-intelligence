from __future__ import annotations

from decimal import Decimal

from pydantic import Field, model_validator

from .agent import InvestigationReport
from .common import ContractModel
from .market import Evidence, Incident


class ExpectedFact(ContractModel):
    contains: str = Field(min_length=1)
    evidence_ids: tuple[str, ...]


class ExpectedOutcome(ContractModel):
    acceptable_classifications: tuple[str, ...]
    required_facts: tuple[ExpectedFact, ...]
    prohibited_claims: tuple[str, ...] = ()
    required_tools: tuple[str, ...] = ()
    maximum_cost_usd: Decimal | None = Field(default=None, ge=0)
    maximum_latency_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def classifications_must_not_be_empty(self) -> ExpectedOutcome:
        if not self.acceptable_classifications:
            raise ValueError("at least one acceptable classification is required")
        return self


class EvaluationCase(ContractModel):
    schema_version: str = "1.0"
    case_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    tags: tuple[str, ...] = ()
    incident: Incident
    available_evidence: tuple[Evidence, ...]
    expected: ExpectedOutcome
    recorded_output: InvestigationReport | None = None
