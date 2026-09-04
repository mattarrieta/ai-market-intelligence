# Product Decisions to Lock In

This register separates settled architecture from product choices that can remain configurable while the platform is built. A provisional choice is a versioned default, not a permanent commitment.

## Locked decisions

| Decision | Choice | Why |
|---|---|---|
| Product | Read-only prediction-market intelligence | Keeps the project focused on surveillance and AI engineering rather than trading risk |
| First source | Kalshi public market data | Provides real contracts, prices, volume, and open interest without website scraping |
| Detection | Deterministic calculations first | Numerical triggers remain reproducible and testable |
| AI role | Investigate incidents after detection | The model explains evidence; it does not invent signals or place trades |
| Evaluation | Golden datasets and CI release gates | Agent changes must demonstrate quality without regressions |
| Cloud | AWS | Matches the deployment goal and supports Bedrock, ECS, S3, SQS, RDS, and CloudWatch |
| Delivery | Local and replayable before cloud deployment | Keeps development inexpensive and failures reproducible |

## Market-universe decisions

| Decision | Provisional default | Status |
|---|---|---|
| Market types | Open binary markets; exclude multivariate combo markets | Provisional |
| Categories | Politics, economics, technology, crypto, weather, and major sports | To lock in |
| Watchlist size | 50 markets | To validate with API volume and local cost |
| Discovery cadence | Every 15 minutes | Provisional |
| Snapshot cadence | Every 60 seconds | Provisional |
| Minimum 24-hour volume | 100 contracts | To calibrate from observed distributions |
| Minimum open interest | 50 contracts | To calibrate from observed distributions |
| Maximum YES spread | $0.20 | To calibrate from observed distributions |
| Time to close | Between 1 hour and 30 days | To lock in |
| Event concentration | Maximum 5 markets from one event | Provisional |
| Category concentration | Maximum 40% from one category | Provisional |
| Ranking | 24-hour volume, open interest, liquidity, and spread quality | Provisional |

The market selector must return a reason for every inclusion and exclusion. Its policy and thresholds will be configuration with a version identifier, not hard-coded business logic.

## Anomaly decisions

| Decision | Provisional default | Must be decided by |
|---|---|---|
| Initial detectors | Price shock, volume spike, liquidity/spread shock | Phase 4 completion |
| Baseline window | Compare short windows with a rolling historical baseline | Phase 4 completion |
| Warm-up history | Do not score until enough observations exist | Phase 4 completion |
| Severity | Normalized 0-10 score with recorded component values | Phase 4 completion |
| Cooldown | Suppress repeated incidents for the same detector and market | Phase 4 completion |
| Cross-market signals | Deferred until single-market baselines work | Phase 8 |
| Learned anomaly model | Shadow mode only until it beats deterministic baselines | Phase 13 |

## Agent and evidence decisions

| Decision | Provisional default | Must be decided by |
|---|---|---|
| Model provider | Amazon Bedrock behind a provider-independent gateway | Phase 6 |
| Agent framework | Explicit state machine; evaluate Strands/AgentCore later | Phase 7 |
| Evidence sources | Official sources first, with a documented allowlist | Phase 8 |
| Tool budget | 12 calls, including at most 3 evidence searches | Phase 7 |
| Time limit | 90 seconds per investigation | Phase 7 |
| Failure behavior | Return `INCONCLUSIVE`; never fill gaps with speculation | Phase 7 |
| Notifications | Optional n8n workflow after core application is reliable | Phase 13 |

## Product and deployment decisions

| Decision | Provisional default | Must be decided by |
|---|---|---|
| First dashboard | Market watchlist, incidents, charts, and investigation trace | Phase 5 |
| Authentication | Single-user demo first | Before public deployment |
| Initial AWS compute | ECS Fargate | Phase 11 |
| Database | RDS PostgreSQL | Phase 11 |
| Monthly AWS budget | Set a hard budget before provisioning | Before Phase 11 |
| Public URL | Decide domain and access policy before deployment | Before Phase 11 |

## Decision order

Decisions should be made only when they affect the next testable milestone:

1. Build replay and deterministic anomaly detection using recorded fixtures.
2. Observe real market distributions and calibrate selector thresholds.
3. Lock the version-one watchlist policy before connecting live detection.
4. Build the API and dashboard around stable incident contracts.
5. Select the Bedrock model through evaluation rather than preference.
6. Lock AWS cost and access controls immediately before provisioning.

## Current delivery picture

| Phase | Status | Outcome |
|---|---|---|
| 1 — Repository and contracts | Complete | Typed domain contracts and CI |
| 2 — Evaluation foundation | Complete | Golden dataset, graders, and release gate |
| 3 — Public Kalshi collector | Implemented; soak run pending | Bounded discovery, normalization, SQLite history, and featured-market selection |
| 4 — Replay and deterministic anomalies | Next | Reproducible features and incidents from recorded data |
| 5 — API and dashboard | Pending | Visible end-to-end product demonstration |
| 6-9 — Model, agent, retrieval, eval UX | Pending | Evidence-grounded agentic investigation |
| 10 — Live WebSocket | Pending | Higher-resolution market monitoring |
| 11 — AWS | Pending | Reproducible deployed application |
| 12-13 — Scale and advanced ML | Optional | Flink, MSK, River, Chronos, and workflows |

## Review rule

At each phase boundary, review only the decisions needed by the following phase. Any changed default must receive a new policy version and be tested through replay so earlier incidents remain reproducible.
