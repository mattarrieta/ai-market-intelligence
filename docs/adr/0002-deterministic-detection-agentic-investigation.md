# ADR 0002: Separate deterministic detection from agentic investigation

- Status: Accepted
- Date: 2026-09-03

## Context

Market calculations must be reproducible, while investigations require semantic interpretation and adaptive evidence gathering.

## Decision

Use deterministic code for features, anomaly rules, event timing, and numerical claims. Invoke a bounded agent only after an incident exists. Give the agent typed, read-only tools and no trading authority.

## Consequences

- Detector results can be replayed and tested exactly.
- Agent behavior can vary without changing numerical evidence.
- Live execution remains outside the agent's authority.
