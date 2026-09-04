# ADR 0001: Begin with a modular monolith

- Status: Accepted
- Date: 2026-09-03

## Context

The target contains ingestion, detection, agent, evaluation, and API components. Their boundaries will change while the domain is being discovered.

## Decision

Begin with one installable Python package containing explicit module and contract boundaries. Extract a separately deployed service only when its scaling, reliability, security, or release requirements differ materially.

## Consequences

- Local development and testing remain simple.
- Contracts stabilize before network boundaries are introduced.
- Future service extraction does not require redefining domain models.
