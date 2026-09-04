# AI Market Intelligence — System Design and Delivery Plan

## 1. Purpose

AI Market Intelligence is an agentic market-surveillance platform. It monitors prediction markets, detects unusual price, volume, and liquidity behavior, and assigns a bounded AI investigator to determine what may have happened. The investigator gathers evidence through approved read-only tools, tests competing explanations, produces a cited report, and records a complete audit trace.

The project has two equally important products:

1. A market-intelligence application that detects and investigates real events.
2. An AI evaluation platform that measures whether agent changes improve or damage quality, factuality, citations, tool use, cost, and latency.

The goal is not to build an LLM chatbot or an autonomous trading bot. The goal is to demonstrate production AI engineering: backend systems, data pipelines, agent orchestration, evaluation, observability, cloud infrastructure, and safe deployment.

## 2. Interview Story

The concise project explanation is:

> I built an agentic prediction-market intelligence platform. Deterministic streaming services detect unusual market behavior. A bounded investigation agent forms competing hypotheses, selects read-only market and evidence tools, and produces a cited report that separates facts, inferences, and speculation. A first-class evaluation platform runs agent versions against reviewed golden datasets, measures quality, factuality, citation accuracy, tool behavior, cost, and latency, and blocks regressions in CI. The system is deployed on AWS with infrastructure as code and end-to-end observability.

## 3. Design Principles

### 3.1 Deterministic calculations, probabilistic interpretation

Normal code calculates prices, returns, z-scores, spreads, order-book imbalance, event timing, and other numerical facts. The LLM interprets those validated facts and chooses what evidence to gather.

### 3.2 Evidence before explanation

The agent must retrieve evidence before producing conclusions. Factual claims reference internal evidence identifiers that can be validated and displayed to users.

### 3.3 Bounded agency

The agent receives read-only tools, a tool-call budget, a token budget, a time limit, approved data sources, and explicit termination conditions. An unresolved investigation is a valid outcome.

### 3.4 Evaluation from the beginning

Every prompt, model, tool, and agent configuration is versioned. Recorded investigations become regression cases. New versions must pass quality gates before deployment.

### 3.5 Local first, AWS second

Each capability must work locally with recorded data before cloud services are introduced. AWS deployment is a packaging and operations milestone, not a prerequisite for validating the product.

### 3.6 No live trading in the initial product

The initial system is read-only. If execution is added later, deterministic strategy and risk services—not an LLM—control orders.

## 4. Scope

### 4.1 Version 1 scope

- Discover open Kalshi markets through the public REST API.
- Normalize exchange-specific data into internal contracts.
- Store timestamped market snapshots.
- Detect price, volume, and liquidity anomalies deterministically.
- Replay recorded market events deterministically.
- Investigate incidents through a bounded tool-using agent.
- Produce structured, cited incident reports.
- Run agent outputs against a versioned golden evaluation dataset.
- Display incidents, investigations, traces, and evaluation results.
- Deploy the working application to AWS.

### 4.2 Explicitly deferred

- Real-money trading
- Multiple prediction-market exchanges
- High-frequency equities ingestion
- Training a proprietary foundation model
- A large multi-agent swarm
- Self-hosting Kafka or Flink on Kubernetes
- Fully autonomous actions outside the application

## 5. High-Level Architecture

```text
Kalshi REST/WebSocket
          |
          v
Market Ingestion Service
          |
          v
Normalized Market Events
          |
          v
Streaming / Replay Pipeline
          |
          v
Feature Calculator
          |
          v
Deterministic Anomaly Detector
          |
          v
Incident Queue
          |
          v
Bounded Investigation Agent
    |          |           |
    v          v           v
Market     Related      Evidence
Tools      Markets       Search
    |          |           |
    +----------+-----------+
               |
               v
Structured Incident Report
               |
       +-------+-------+
       |               |
       v               v
PostgreSQL       Evaluation Platform
       |               |
       +-------+-------+
               |
               v
       FastAPI + Next.js UI
```

## 6. Major Components

### 6.1 Market ingestor

Responsibilities:

- Discover markets with Kalshi REST endpoints.
- Connect to authenticated WebSocket channels later.
- Validate and normalize inbound messages.
- Attach exchange and received timestamps.
- Handle reconnects, pagination, rate limits, and malformed messages.
- Publish normalized events without embedding anomaly logic.

Initial technology:

- Python 3.11+
- `httpx` for REST
- `websockets` for live streams
- Pydantic for contracts
- Structured JSON logging

### 6.2 Replay engine

Responsibilities:

- Record normalized events to line-delimited JSON or Parquet.
- Replay events in original event-time order.
- Support accelerated and step-by-step playback.
- Reproduce detector and agent demonstrations when live markets are quiet.
- Make integration and regression tests deterministic.

Initial technology:

- Python
- JSONL for early fixtures
- S3 and Parquet for the later historical archive

### 6.3 Feature calculator

Calculates per-market rolling features:

- Midpoint and spread
- 30-second and 5-minute probability-point changes
- Windowed trade volume
- Rolling volume mean and deviation
- Volatility
- YES/NO book depth
- Order-book imbalance
- Liquidity decline
- Data freshness and market health state

Initial implementation uses Python rolling windows. Apache Flink is introduced only after the event contracts and calculations are stable.

### 6.4 Anomaly detector

The first detector family is deterministic:

- Price shock
- Volume spike
- Spread anomaly
- Order-book imbalance
- Liquidity disappearance

Each incident records the feature values, thresholds, detector version, market health, and evidence needed to reproduce the decision.

Later detector families may include:

- River online anomaly detection
- Forecast-residual detection using Chronos-2
- Cross-market divergence detection

ML models supplement deterministic rules; they do not silently replace them.

### 6.5 Model gateway

All LLM calls pass through a provider-independent gateway.

Responsibilities:

- Support Amazon Bedrock first and another provider later.
- Validate structured outputs.
- Record provider, model, prompt, and schema versions.
- Enforce timeouts, retries, rate limits, and token budgets.
- Calculate request cost.
- Provide deterministic mocks for tests.
- Support controlled model rollouts and future failover.

### 6.6 Investigation agent

The agent follows an explicit state machine:

```text
CREATED
   |
   v
PLANNING
   |
   v
GATHERING_EVIDENCE
   |
   v
TESTING_HYPOTHESES
   |
   v
CRITIQUING
   |
   v
REVISING
   |
   v
COMPLETED / INCONCLUSIVE / FAILED
```

The agent:

1. Reads the validated incident.
2. Interprets the market contract.
3. Forms competing hypotheses.
4. Selects read-only tools.
5. Updates hypotheses using returned evidence.
6. Produces a structured draft.
7. Runs a critic and deterministic validation.
8. Revises or returns an inconclusive result.

Initial limits:

- Maximum 12 tool calls
- Maximum 3 evidence searches
- Maximum 90 seconds
- Configurable token and cost budget
- No write or trading tools

### 6.7 Tool platform

Initial tools:

- `market.get_incident`
- `market.get_contract`
- `market.get_window`
- `market.find_related`
- `market.compare_timing`
- `evidence.search_official_sources`
- `evidence.retrieve_document`
- `analysis.cross_market_confirmation`

Every tool has a typed input/output schema and records:

- Tool and schema version
- Arguments
- Start and finish timestamps
- Result evidence identifiers
- Success or failure category
- Retry count
- Trace identifier

### 6.8 Evaluation platform

The evaluation platform is a central product feature.

It runs a matrix of:

```text
Golden dataset
    x agent version
    x prompt version
    x model version
    x tool version
```

Initial deterministic metrics:

- Output-schema validity
- Classification accuracy or allowed-class match
- Required-fact coverage
- Prohibited-claim detection
- Citation validity
- Required-tool recall
- Tool-call budget compliance
- Cost
- Total and per-tool latency

Later semantic metrics:

- Evidence entailment
- Summary completeness
- Fact/inference/speculation separation
- Hypothesis quality
- Unnecessary tool use
- Confidence calibration

Golden cases contain the incident, available evidence, acceptable classifications, required facts, prohibited claims, expected citations, and acceptable tool behavior.

### 6.9 Critic and validators

Deterministic validators reject:

- Invalid schemas
- Unknown evidence identifiers
- Numerical claims that disagree with incident data
- Missing citations for externally sourced facts
- Invented market tickers
- Budget violations

An independent critic model reviews subjective properties but cannot override deterministic failures.

### 6.10 Backend API

FastAPI endpoints eventually include:

```text
GET  /health
GET  /markets
GET  /markets/{ticker}
GET  /incidents
GET  /incidents/{id}
POST /incidents/{id}/investigate
GET  /investigations/{id}
GET  /investigations/{id}/trace
POST /investigations/{id}/feedback
POST /evaluations/runs
GET  /evaluations/runs
GET  /evaluations/runs/{id}
```

### 6.11 Frontend

Next.js and TypeScript provide:

- Live market overview
- Incident list and severity filters
- Incident price/volume/liquidity chart
- Structured agent report
- Evidence viewer
- Step-by-step agent trace
- Evaluation run comparison
- Failed-case explorer
- Human feedback controls

### 6.12 Workflow automation

n8n is optional and remains outside the market-data path. It may later manage:

- Slack or email alerts
- Human approval for expensive investigations
- Daily intelligence summaries
- Ticket creation
- Feedback routing

Critical backend workflows use application code, queues, and AWS Step Functions rather than n8n.

## 7. Technology Decisions

| Area | Initial choice | Later production choice | Reason |
|---|---|---|---|
| Backend | Python + FastAPI | Same | Matches applied-AI and backend roles |
| Contracts | Pydantic | Same | Strict validation and JSON Schema |
| Database | PostgreSQL | Amazon RDS PostgreSQL | Reliable relational and JSON storage |
| Vector search | pgvector | pgvector or OpenSearch | Related-market and evidence retrieval |
| Frontend | Next.js + TypeScript | Same | Internal-tool and AI-product experience |
| Local queue | In-process adapter | Amazon SQS | Simple durable investigation jobs |
| Event stream | Local replay | Amazon MSK | Durable market-event replay |
| Stream processing | Python windows | Managed Apache Flink | Event-time stateful processing |
| Model access | Mock gateway | Amazon Bedrock | AWS-native managed inference |
| Agent runtime | Explicit state machine / Strands | Bedrock AgentCore Runtime | Bounded, observable agents |
| Agent tools | Python typed functions | AgentCore Gateway | Governed tool access |
| Object storage | Local files | Amazon S3 | Raw events and evaluation artifacts |
| Containers | Docker Compose | ECS first, EKS if justified | Local parity without premature Kubernetes |
| Infrastructure | None initially | Terraform | Reproducible AWS environments |
| CI/CD | GitHub Actions | GitHub Actions | Tests and evaluation release gates |
| Observability | Structured logs | OpenTelemetry + CloudWatch | End-to-end diagnostics |
| Workflow UI | None initially | Optional n8n | Human and third-party automation |
| Online ML | None initially | River | Incremental anomaly scoring |
| Forecast model | None initially | Chronos-2 on SageMaker | Probabilistic forecast residuals |

## 8. Core Data Contracts

### 8.1 Normalized market event

```json
{
  "event_id": "uuid",
  "source": "kalshi",
  "event_type": "TRADE",
  "ticker": "KXFED-SEP",
  "exchange_timestamp": "2026-08-30T14:01:02.421Z",
  "received_timestamp": "2026-08-30T14:01:02.438Z",
  "price": 0.62,
  "quantity": 100,
  "schema_version": "1.0"
}
```

### 8.2 Incident

```json
{
  "incident_id": "uuid",
  "ticker": "KXFED-SEP",
  "type": "PRICE_SHOCK",
  "detected_at": "2026-08-30T14:01:03Z",
  "severity": 8.4,
  "features": {
    "price_change_30s": 0.16,
    "volume_zscore": 6.8,
    "book_imbalance": 0.81
  },
  "detector_version": "rules-1.0.0"
}
```

### 8.3 Investigation report

```json
{
  "classification": "UNEXPLAINED_INFORMATION_EVENT",
  "confidence": 0.78,
  "summary": "...",
  "facts": [
    {
      "claim": "The YES price increased by 16 probability points.",
      "evidence_ids": ["market-window-17"]
    }
  ],
  "inferences": [],
  "speculation": [],
  "unknowns": [],
  "agent_version": "investigator-1.0.0",
  "prompt_version": "investigator-prompt-1",
  "model_version": "configured-at-runtime"
}
```

## 9. Repository Structure

```text
ai-market-intelligence/
|-- services/
|   |-- market-ingestor/
|   |-- anomaly-detector/
|   |-- model-gateway/
|   |-- investigation-agent/
|   |-- eval-runner/
|   `-- api/
|-- frontend/
|-- packages/
|   |-- market-contracts/
|   |-- agent-contracts/
|   |-- tool-contracts/
|   |-- evaluation/
|   `-- observability/
|-- datasets/
|   |-- recorded-events/
|   `-- golden/
|-- prompts/
|   |-- investigator/
|   `-- critic/
|-- infra/
|   |-- terraform/
|   `-- containers/
|-- tests/
|   |-- unit/
|   |-- integration/
|   |-- replay/
|   `-- evals/
|-- docs/
|-- docker-compose.yml
|-- pyproject.toml
`-- README.md
```

The initial repository may use a single Python package while boundaries stabilize. Services are separated only when independent deployment or scaling is justified.

## 10. AWS Target Architecture

```text
Internet
   |
   v
Application Load Balancer
   |
   +--------------------+
   |                    |
   v                    v
FastAPI service      Next.js frontend
   |
   +--> RDS PostgreSQL + pgvector
   +--> SQS investigation queue
   +--> S3 event/evaluation artifacts
   +--> Bedrock / AgentCore
   +--> CloudWatch / OpenTelemetry

Market ingestor --> MSK --> Managed Flink --> incident topic --> SQS
```

Deployment order:

1. Dockerized application on ECS or App Runner.
2. RDS, S3, SQS, Secrets Manager, and CloudWatch.
3. Bedrock model access and AgentCore.
4. MSK and Managed Flink only after the local streaming design is proven.
5. EKS only if multiple workloads make Kubernetes operationally justified.

## 11. Security and Safety

- No credentials in source control.
- Secrets stored in AWS Secrets Manager.
- Least-privilege IAM roles per service.
- Read-only agent tools.
- Evidence-source allowlist.
- Request and output schema validation.
- Encryption in transit and at rest.
- Audit log for every agent and tool action.
- Human approval before future consequential actions.
- No LLM-controlled trading.

## 12. Observability

Every investigation has one trace identifier spanning:

```text
incident -> queue -> agent -> model calls -> tool calls -> validators -> report
```

Important metrics:

- Events received per second
- Stale or malformed events
- Incidents by type and severity
- Queue depth and investigation wait time
- Investigation success and inconclusive rates
- Tool failures and retries
- Model tokens and cost
- End-to-end latency and P95/P99 latency
- Evaluation pass rate
- Factuality and citation regressions

## 13. Testing Strategy

### Unit tests

- Schema validation
- Feature calculations
- Detector thresholds
- Order-book updates
- Tool argument validation
- Deterministic graders

### Integration tests

- Recorded Kalshi response to normalized event
- Event to incident
- Incident to investigation report with mock model
- Database persistence
- Queue retry and idempotency

### Replay tests

- Reproduce incidents from recorded streams.
- Confirm duplicate and out-of-order event handling.
- Confirm restart produces the same detector results.

### AI evaluations

- Run recorded and live candidate outputs against golden cases.
- Compare candidate metrics with the production baseline.
- Fail CI for critical quality regressions.

## 14. Ordered Implementation Plan

Only one phase is implemented at a time. The next phase begins after the current phase meets its exit criteria and is reviewed.

### Phase 0 — Design approval

Deliverables:

- This design document
- Agreed product scope
- Agreed technology choices
- Agreed implementation order

Exit criteria:

- User approves or revises the design.
- No application code is required.

### Phase 1 — Repository and contracts

Deliverables:

- Python project configuration
- Formatting, linting, and testing configuration
- Pydantic contracts for events, incidents, evidence, tools, reports, and evaluations
- Architecture decision records for important choices
- GitHub Actions unit-test workflow

Exit criteria:

- Project installs from a clean environment.
- Contract tests pass.
- CI runs successfully.
- No live external dependencies are required.

### Phase 2 — Evaluation platform foundation

Deliverables:

- JSONL golden-dataset format
- Initial 10 reviewed or synthetic cases
- Deterministic graders
- Aggregate evaluation report
- Cost and latency accounting
- CI quality gate

Exit criteria:

- A deliberately bad recorded output fails for the correct reason.
- A valid recorded output passes.
- CI blocks a factuality or citation regression.
- Results are reproducible without an API key.

### Phase 3 — Public Kalshi REST collector

Deliverables:

- Market discovery client
- Pagination, timeout, retry, and validation behavior
- Normalized market snapshots
- Local persistence
- Recorded API fixtures

Exit criteria:

- Collector runs for at least one hour without manual intervention.
- Tests use fixtures rather than live network calls.
- Downstream code does not depend on Kalshi response objects.

### Phase 4 — Replay engine and deterministic anomalies

Deliverables:

- Event recorder and replay CLI
- Rolling feature calculation
- Price-shock, volume-spike, and liquidity-shock detectors
- Incident persistence
- Cooldown and deduplication

Exit criteria:

- Recorded input produces identical incidents across repeated runs.
- Quiet fixtures produce no false incidents.
- Synthetic anomalies trigger expected incidents.

### Phase 5 — Backend API and basic dashboard

Deliverables:

- FastAPI market and incident endpoints
- PostgreSQL migrations
- Next.js market and incident views
- Docker Compose development environment

Exit criteria:

- User can replay a fixture and inspect the resulting incident in the UI.
- Health checks and structured logs work.
- Core paths have integration tests.

### Phase 6 — Model gateway

Deliverables:

- Provider-independent model interface
- Mock provider
- Bedrock provider
- Structured-output validation
- Prompt/model versioning
- Token, cost, latency, retry, and timeout tracking

Exit criteria:

- Same request runs through mock and Bedrock adapters.
- Invalid model output is rejected.
- Every model request is traceable and costed.

### Phase 7 — Bounded investigation agent

Deliverables:

- Agent state machine
- Hypothesis representation
- Initial read-only market tools
- Tool-call, token, time, and cost budgets
- Structured reports
- Investigation persistence and recovery

Exit criteria:

- Agent investigates a stored incident using mock tools.
- Interrupted investigation resumes safely.
- Budget exhaustion returns an inconclusive report.
- All actions appear in an audit trace.

### Phase 8 — Retrieval and related markets

Deliverables:

- Market semantic extraction
- Embeddings and pgvector index
- Related-market retrieval
- Official-source document ingestion
- Evidence search and timing comparison

Exit criteria:

- Reviewed examples retrieve relevant related markets.
- Reports cite only known evidence identifiers.
- Retrieval metrics are included in evaluations.

### Phase 9 — Critic, semantic evals, and trace explorer

Deliverables:

- Independent critic pass
- Semantic evidence-entailment grader
- Baseline-versus-candidate comparisons
- Evaluation and trace dashboard
- Human feedback capture

Exit criteria:

- Unsupported claims are rejected or revised.
- Candidate regressions are visible by case and metric.
- Reviewed feedback can become a new golden case.

### Phase 10 — WebSocket and order-book processing

Deliverables:

- Authenticated Kalshi WebSocket client
- Snapshot and delta reconstruction
- Sequence-gap detection
- Reconnection and snapshot recovery
- Live order-book anomaly features

Exit criteria:

- Reconstructed books match REST snapshots within documented tolerances.
- Disconnect and missing-sequence tests pass.
- Market health changes correctly between live, stale, and recovering.

### Phase 11 — AWS deployment

Deliverables:

- Docker images
- Terraform modules
- ECS/App Runner service
- RDS, S3, SQS, Secrets Manager, and CloudWatch
- Bedrock/AgentCore deployment
- CI/CD deployment workflow

Exit criteria:

- A clean AWS environment can be provisioned from Terraform.
- The deployed application completes a recorded investigation.
- Secrets are not present in images, logs, or repository history.
- Alerts and traces are visible in CloudWatch.

### Phase 12 — Streaming scale

Deliverables:

- Amazon MSK
- Managed Apache Flink feature jobs
- Schema evolution strategy
- Consumer-lag and checkpoint monitoring
- Load and failure testing

Exit criteria:

- The streaming path meets a documented latency target.
- Events can be replayed without duplicate incidents.
- Failure recovery and backpressure behavior are demonstrated.

### Phase 13 — Advanced ML and workflows

Optional deliverables:

- River online anomaly model
- Chronos-2 forecast-surprise scoring
- Cross-market graph divergence
- n8n notification and approval templates
- Shadow-mode strategy research

Each addition must outperform or complement existing baselines in recorded evaluations before becoming part of the production score.

## 15. Progress Tracking

Each phase will use the following status format:

```text
Phase: 2 — Evaluation platform foundation
Status: IN PROGRESS

Completed:
- Golden-case schema
- Classification grader

Current:
- Citation grader

Remaining:
- Cost/latency summary
- CI release gate

Verification:
- 18 unit tests passing
- 10/10 valid golden cases passing
- 3/3 intentionally bad cases rejected
```

At the end of every phase:

1. Run the phase-specific tests.
2. Summarize files and behavior added.
3. Show verification results.
4. Commit the completed phase separately.
5. Ask for review before beginning the next phase.

## 16. Current Status and Decision Register

Phases 1 and 2 are complete. Phase 3 has a verified public Kalshi collector, normalized snapshots, local persistence, and bounded featured-market selection; its longer soak run remains pending. Phase 4 is the next implementation phase.

Product choices that should remain configurable—including market categories, eligibility thresholds, watchlist size, detector calibration, agent budgets, and AWS cost controls—are tracked in [Product Decisions to Lock In](docs/PRODUCT-DECISIONS.md).

The immediate build order is:

1. Implement replay from recorded snapshots.
2. Calculate deterministic rolling features.
3. Emit reproducible price, volume, and liquidity incidents.
4. Use observed distributions to calibrate the market-selector defaults.
5. Lock the version-one market policy before enabling continuous live detection.

This keeps the core detector exchange-independent and prevents an early category preference from becoming an architectural dependency.
