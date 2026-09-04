from decimal import Decimal

from market_intelligence.contracts import ClaimKind, EvaluationCase, InvestigationReport

from .models import CaseEvaluation


def _contains(text: str, fragment: str) -> bool:
    return fragment.casefold() in text.casefold()


def evaluate_case(case: EvaluationCase, report: InvestigationReport) -> CaseEvaluation:
    """Grade one structured agent report using reproducible checks."""

    failures: list[str] = []
    classification_score = Decimal(
        int(report.classification in case.expected.acceptable_classifications)
    )
    if classification_score == 0:
        failures.append(f"unexpected classification: {report.classification}")

    factual_claims = [claim for claim in report.claims if claim.kind is ClaimKind.FACT]
    searchable_text = " ".join([report.summary, *(claim.text for claim in report.claims)])
    matched_facts = 0
    correct_citations = 0

    available_evidence = {evidence.evidence_id for evidence in case.available_evidence}
    all_citations = {item for claim in report.claims for item in claim.evidence_ids}
    unknown_citations = sorted(all_citations - available_evidence)
    failures.extend(f"unknown evidence_id: {item}" for item in unknown_citations)

    for expected_fact in case.expected.required_facts:
        matches = [
            claim for claim in factual_claims if _contains(claim.text, expected_fact.contains)
        ]
        if not matches:
            failures.append(f"missing required fact: {expected_fact.contains}")
            continue
        matched_facts += 1
        required_ids = set(expected_fact.evidence_ids)
        if any(required_ids.issubset(set(claim.evidence_ids)) for claim in matches):
            correct_citations += 1
        else:
            failures.append(f"incorrect citation for fact: {expected_fact.contains}")

    prohibited = [
        text for text in case.expected.prohibited_claims if _contains(searchable_text, text)
    ]
    failures.extend(f"prohibited claim present: {text}" for text in prohibited)

    required_fact_count = len(case.expected.required_facts)
    factuality_score = (
        Decimal(matched_facts) / Decimal(required_fact_count) if required_fact_count else Decimal(1)
    )
    citation_score = (
        Decimal(correct_citations) / Decimal(required_fact_count)
        if required_fact_count
        else Decimal(1)
    )
    if prohibited:
        factuality_score = Decimal(0)
    if unknown_citations:
        citation_score = Decimal(0)

    successful_tools = {trace.tool_name for trace in report.tool_calls if trace.succeeded}
    required_tools = set(case.expected.required_tools)
    missing_tools = sorted(required_tools - successful_tools)
    failures.extend(f"required tool not called successfully: {tool}" for tool in missing_tools)
    tool_score = (
        Decimal(len(required_tools & successful_tools)) / Decimal(len(required_tools))
        if required_tools
        else Decimal(1)
    )

    maximum_cost = case.expected.maximum_cost_usd
    cost_within_limit = maximum_cost is None or report.usage.estimated_cost_usd <= maximum_cost
    if not cost_within_limit:
        failures.append("cost limit exceeded")

    maximum_latency = case.expected.maximum_latency_ms
    latency_within_limit = maximum_latency is None or report.usage.latency_ms <= maximum_latency
    if not latency_within_limit:
        failures.append("latency limit exceeded")

    return CaseEvaluation(
        case_id=case.case_id,
        classification_score=classification_score,
        factuality_score=factuality_score,
        citation_score=citation_score,
        tool_score=tool_score,
        cost_within_limit=cost_within_limit,
        latency_within_limit=latency_within_limit,
        estimated_cost_usd=report.usage.estimated_cost_usd,
        latency_ms=report.usage.latency_ms,
        failures=tuple(failures),
    )
