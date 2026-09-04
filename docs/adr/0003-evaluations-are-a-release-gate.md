# ADR 0003: Treat AI evaluations as a release gate

- Status: Accepted
- Date: 2026-09-03

## Context

Unit tests cannot detect regressions in classification, factuality, citations, tool selection, cost, or latency caused by model and prompt changes.

## Decision

Maintain versioned golden datasets and run deterministic and semantic graders in CI. Candidate agent configurations must satisfy absolute quality thresholds and regression limits before deployment.

## Consequences

- Prompts, tools, models, datasets, and agent configurations require versions.
- Evaluation results become durable artifacts.
- Deterministic recorded-output evaluation remains available without cloud credentials.
