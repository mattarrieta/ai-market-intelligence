from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from market_intelligence.contracts import Claim, ClaimKind, InvestigationBudget, ToolCallTrace

UTC_NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


def test_fact_requires_evidence() -> None:
    with pytest.raises(ValidationError, match="facts must cite"):
        Claim(kind=ClaimKind.FACT, text="The price moved.")


def test_inference_may_have_no_direct_citation() -> None:
    claim = Claim(kind=ClaimKind.INFERENCE, text="The move may be information-driven.")
    assert claim.evidence_ids == ()


def test_tool_trace_rejects_finish_before_start() -> None:
    with pytest.raises(ValidationError, match="finished_at"):
        ToolCallTrace(
            trace_id="trace-1",
            tool_name="market.get_window",
            tool_version="1.0",
            started_at=UTC_NOW,
            finished_at=UTC_NOW - timedelta(seconds=1),
            succeeded=True,
        )


def test_successful_tool_trace_cannot_have_error() -> None:
    with pytest.raises(ValidationError, match="error_category"):
        ToolCallTrace(
            trace_id="trace-1",
            tool_name="market.get_window",
            tool_version="1.0",
            started_at=UTC_NOW,
            finished_at=UTC_NOW,
            succeeded=True,
            error_category="TIMEOUT",
        )


def test_budget_has_bounded_defaults() -> None:
    budget = InvestigationBudget()
    assert budget.max_tool_calls == 12
    assert budget.max_cost_usd == Decimal("1.00")
