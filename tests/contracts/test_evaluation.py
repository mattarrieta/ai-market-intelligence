from decimal import Decimal

import pytest
from pydantic import ValidationError

from market_intelligence.contracts import ExpectedOutcome


def test_expected_outcome_requires_classification() -> None:
    with pytest.raises(ValidationError, match="acceptable classification"):
        ExpectedOutcome(acceptable_classifications=(), required_facts=())


def test_expected_outcome_accepts_quality_limits() -> None:
    outcome = ExpectedOutcome(
        acceptable_classifications=("LIQUIDITY_DRIVEN",),
        required_facts=(),
        maximum_cost_usd=Decimal("0.10"),
        maximum_latency_ms=20_000,
    )
    assert outcome.maximum_cost_usd == Decimal("0.10")
