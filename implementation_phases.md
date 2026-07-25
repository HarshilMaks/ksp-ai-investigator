# KSP InvestigateAI Implementation Phases

> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: `.LOCK/DECISIONS.md` (2026-07-24)
> Knowledge base: `.LOCK/*.md`, ingested in the user-mandated order
> Plan version: 1.0.0
> Last reviewed: 2026-07-24
> Current phase: `P02`
> Current state: `IN_PROGRESS`

## 1. Operating Contract

This file is the implementation state machine for the repository. The implementation is executed strictly in phase order. A phase cannot become `COMPLETE` until its acceptance checks and review gate have concrete evidence recorded in that phase. Only one phase may be `IN_PROGRESS` at a time.

The locked system is a **Crime Intelligence Operating System**, not a chatbot:

```text
Investigation → question → deterministic evidence → updated workspace → next action
```

The governing rule is:

```text
AI interprets intent and explains evidence.
Deterministic engines compute facts.
Humans review consequential conclusions.
```

### Non-negotiable constraints

- Backend implementation language is Python; do not add a second backend language.
- Catalyst Data Store is authoritative for structured and vector records; Neo4j 5 Community on AppSail is a graph projection/query store.
- The raw PostgreSQL DDL in `.LOCK/database-schema.md` is a logical reference until Catalyst compatibility is validated; do not treat it as deployable Catalyst DDL without validation evidence.
- LangGraph is a deterministic state-machine orchestrator, not an LLM agent.
- Only Planner, Reasoner, and Reporter are LLM-powered reasoning stages.
- Agents/reasoning stages never access databases directly; all access goes through authorized typed T01–T23 tools and deterministic engines.
- Facts, counts, paths, scores, dates, totals, and forecasts come from deterministic engines. LLM output is grounded communication or structured reasoning over validated results.
- Evidence/Explainability is a mandatory release gate for every response and package.
- No literal private chain-of-thought is exposed or persisted; store structured rationale, provenance, citations, uncertainty, and audit metadata.
- Initial data is synthetic only. Do not ingest real police, PII, or sensitive operational data.
- External communication is REST capability/resource APIs, SSE, and multipart REST. WebSockets, gRPC, and MCP are not initial runtime dependencies.
- Do not claim performance, accuracy, capacity, quality, cost, or legal admissibility until measured or separately reviewed.
- `.LOCK/TODO.md` and `session-ses_0754.md` are private and must not be modified, tracked, or included in implementation artifacts.
- No commits or pushes are part of this workflow unless explicitly requested.

### Repository structure decision for implementation

The locked documents contain both an older `functions/` layout and an `src/` orchestrator entry point. The implementation resolves this without changing locked documents:

- `src/` is the shared Python domain, engines, registry, orchestration, adapters, and tests-facing core named by `.LOCK/AGENTS.md`.
- `functions/` contains thin Catalyst HTTP/event/job adapters named by `.LOCK/architecture.md`; adapters delegate to `src/` and contain no duplicated business logic.
- `client/` is the Next.js 15 App Router + React 19 + TypeScript frontend on Catalyst AppSail, organized with Feature-Sliced Design under `client/src/`.
- `appsail/neo4j/` contains the Neo4j container and schema/projection assets.
- `data/` contains synthetic generators, seeds, and explicitly non-sensitive fixtures.
- `.LOCK/` remains source documentation only; it is not modified by implementation phases.

## 2. State Machine

### State fields

Every phase record must maintain these fields:

| Field | Required meaning |
|---|---|
| `id` | Stable phase identifier (`P01`–`P20`) |
| `name` | Human-readable phase name |
| `status` | `PLANNED`, `IN_PROGRESS`, `BLOCKED`, `COMPLETE`, or `SKIPPED` |
| `dependencies` | Earlier phases that must be complete |
| `started_at` | UTC timestamp when work begins |
| `completed_at` | UTC timestamp only after the review gate passes |
| `owner_scope` | Code/docs/config areas changed by the phase |
| `tasks` | Ordered implementation actions |
| `files` | Files to create/modify, including tests and deployment assets |
| `acceptance_criteria` | Observable behavior required for completion |
| `review_gate` | Architecture/data/security/config checks required before completion |
| `validation_commands` | Commands to run for concrete evidence |
| `evidence` | Dated command output, test result, or file assertion; no unsupported claims |
| `notes` | Risks, blockers, and deviations requiring explicit review |

### Transition rules

```text
PLANNED --start--> IN_PROGRESS
IN_PROGRESS --blocked--> BLOCKED
BLOCKED --unblock--> IN_PROGRESS
IN_PROGRESS --all acceptance + review evidence--> COMPLETE
```

A phase may not be started if a dependency is not `COMPLETE`. If validation fails, the phase remains `IN_PROGRESS` and the defect is fixed before transition. `SKIPPED` requires a written reason and explicit architecture review; it is not the default path.

## 3. Review Gate Applied to Every Phase

Before changing a phase to `COMPLETE`, verify and record:

1. **Locked alignment:** `.LOCK/DECISIONS.md`, `.LOCK/architecture.md`, `.LOCK/ai-architecture.md`, and `.LOCK/AGENTS.md` remain authoritative and unchanged.
2. **Schema alignment:** implementation matches `.LOCK/database-schema.md` tables, field semantics, status values, relationships, provenance, card metadata, and audit requirements; logical Catalyst incompatibilities are isolated and documented.
3. **Ontology/workflow alignment:** entity and relationship vocabulary follows `.LOCK/ontology.md` and `.LOCK/crime-domain.md`; flow follows `.LOCK/investigation-workflow.md` and `.LOCK/investigation-engine.md`.
4. **Workspace/card alignment:** persistent state and seven panels follow `.LOCK/investigation-workspace.md`; card payloads, lifecycle, freshness, provenance, confidence, and human-review markers follow `.LOCK/intelligence-cards.md`.
5. **Scenario alignment:** affected behavior maps to `.LOCK/investigation-scenarios.md`; no synthetic scenario is presented as real data or achieved benchmark evidence.
6. **Tool ownership:** every T01–T23 action is typed, authorized, audited, and delegated to the correct deterministic engine or allowed reasoning stage; no public route bypasses the registry.
7. **Configuration:** connection strings, ports, timeouts, environment variables, model names, feature flags, and Catalyst boundaries are checked against the lock. Neo4j Bolt is port `7687`; HTTP `7474` is disabled in production; API timeout target is `30s`, signal `60s`, job `300s` pending deployment validation.
8. **Security:** no secrets are committed; RBAC scope, masking, investigation scope, audit metadata, hash-chain behavior, synthetic-only policy, and human review gates are preserved.
9. **Validation:** targeted tests, formatting/lint/type checks where configured, and a minimal smoke test are run. Results are copied into the phase `evidence` field.
10. **Change scope:** `git diff --check`, `git status`, and an explicit check confirm `.LOCK/TODO.md` and the ignored session file were not modified or tracked.

## 4. Ordered Implementation Phases

### P01 — Repository and environment baseline

- **Status:** `COMPLETE`
- **Dependencies:** none
- **Owner scope:** repository contract, tooling, validation harness, investigator journey
- **Tasks:**
  1. Record Python/Node/tool availability and repository baseline.
  2. Establish the `src/`, `functions/`, `client/`, `data/`, `appsail/`, and `tests/` boundaries without introducing runtime logic.
  3. Add contributor/setup documentation that distinguishes local adapters from Catalyst deployment.
  4. Add a derived `docs/investigator-journey.md` north star: one officer's day from proactive alert through investigation, evidence, hypothesis, health review, report, and closure. Keep it explicitly derived from the locked workspace/workflow/scenario documents.
  5. Add baseline validation commands and private-file protections.
- **Files:** `README.md`, `.gitignore` only if required, `pyproject.toml`, `uv.lock`, `tests/smoke/test_repository_contract.py`, `docs/setup.md`, `docs/investigator-journey.md`.
- **Acceptance criteria:** clean Python test entry point exists; required directories are explicit; the investigator journey starts with intelligence before a query and includes evidence board, hypothesis for/against/missing state, Investigation Health, human ownership, and closure; no secret or private session file is tracked; backend remains Python-only.
- **Review gate:** verify the architecture-layout conflict is resolved by core `src/` plus thin `functions/` adapters; verify `.LOCK` is untouched.
- **Validation:** `uv --version`; `uv run python --version`; `uv run python -m unittest discover -s tests -p 'test_*.py'`; `git diff --check`; `git status --short --ignored`.
- **Evidence:** record exact outputs and file assertions here.
- **Notes:** do not install dependencies or call external services in this phase.

### P02 — Python backend scaffold and configuration

- **Status:** `IN_PROGRESS`
- **Dependencies:** `P01`
- **Owner scope:** Python package, pinned dependencies, typed configuration
- **Tasks:** create package boundaries for `src/shared`, `src/domain`, `src/engines`, `src/registry`, `src/orchestration`, `src/adapters`; implement environment parsing and validation; add `.env.example`; pin dependencies; standardize error envelopes and request IDs.
- **Files:** `pyproject.toml`, `requirements.txt` or lock-equivalent, `.env.example`, `src/shared/config.py`, `src/shared/errors.py`, `src/shared/clock.py`, package `__init__.py` files, `tests/unit/shared/`.
- **Acceptance criteria:** startup configuration validates required/optional variables without printing secrets; all declared ports/timeouts/model IDs are represented; invalid configuration fails clearly.
- **Review gate:** verify `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, Data Store/Catalyst configuration, four LLM keys, model chain, API/job/signal timeouts, and no hardcoded credentials.
- **Validation:** `uv run python -m unittest discover -s tests -p 'test_*.py'`; `uv run python -m compileall src functions`; formatter/linter/type checker configured by P01.
- **Evidence:** record test and static-check output.
- **Notes:** Catalyst SDK calls remain behind adapters; local fallback implementations are explicit.

### P03 — Catalyst integration boundaries and local adapters

- **Status:** `PLANNED`
- **Dependencies:** `P02`
- **Owner scope:** Catalyst Data Store, Cache, Stratus, Signals, Cron, Circuits, Auth boundaries
- **Tasks:** define typed ports/interfaces; implement local in-memory/file adapters for development; add Catalyst adapter stubs with validated request/response shapes; implement Neo4j client boundary with Bolt port `7687`; add LiteLLM model-router boundary.
- **Files:** `src/shared/ports.py`, `src/adapters/catalyst/`, `src/adapters/neo4j.py`, `src/adapters/llm.py`, `src/adapters/cache.py`, `src/adapters/stratus.py`, `functions/shared/` thin wrappers, `tests/unit/adapters/`.
- **Acceptance criteria:** engines depend on interfaces rather than vendor SDKs; local tests run without Catalyst/Neo4j/LLM credentials; external calls are disabled unless explicitly configured.
- **Review gate:** confirm REST/SSE/multipart are the only initial external protocols; no direct database access from agents; connection strings and TLS/auth settings are centralized.
- **Validation:** adapter contract tests; config smoke test; no-network default test.
- **Evidence:** record outputs and any Catalyst compatibility limitations.

### P04 — Logical data contracts and synthetic fixtures

- **Status:** `PLANNED`
- **Dependencies:** `P02`, `P03`
- **Owner scope:** domain models, schema mapping, synthetic data
- **Tasks:** model FIRs, entities, FIR-entity links, relationships, investigations, evidence, timeline, engine runs, provenance, cards, and audit records; implement Karnataka/CCTNS identifiers and IPC/BNS mappings; create deterministic synthetic fixture generators; document logical-to-Catalyst mapping gaps.
- **Files:** `src/domain/models.py`, `src/domain/enums.py`, `src/domain/ontology.py`, `src/domain/schema_mapping.py`, `data/generator/`, `data/seed/`, `tests/unit/domain/`, `docs/data-contracts.md`.
- **Acceptance criteria:** models enforce locked status/role/type values and confidence bounds; fixtures contain no real sensitive data; generated FIR numbers and station codes follow locked formats; every relationship can carry evidence/provenance.
- **Review gate:** compare model fields to `.LOCK/database-schema.md`, `.LOCK/ontology.md`, and `.LOCK/crime-domain.md`; explicitly flag non-portable PostgreSQL constructs rather than silently using them.
- **Validation:** model validation tests; fixture reproducibility test; schema assertion script.
- **Evidence:** record generated counts, checksums, and assertion output.

### P05 — Neo4j projection and graph schema

- **Status:** `PLANNED`
- **Dependencies:** `P04`
- **Owner scope:** graph projection, constraints, indexes, local AppSail container
- **Tasks:** implement idempotent Catalyst-authoritative-to-Neo4j projection; add labels, relationship properties, constraints, indexes, bounded traversal helpers; add AppSail Docker configuration with port `7687`, production HTTP restriction, memory settings, health check, and backup/export boundary.
- **Files:** `appsail/neo4j/Dockerfile`, `appsail/neo4j/neo4j.conf`, `appsail/neo4j/import/schema.cypher`, `appsail/neo4j/scripts/`, `src/engines/graph_intelligence.py`, `tests/integration/graph/`.
- **Acceptance criteria:** synthetic entities/FIRs project idempotently; required relationship evidence and verification properties survive projection; bounded traversal/path queries return citations; health check detects unavailable graph.
- **Review gate:** validate labels and relationship types against ontology/schema; check Bolt URI/port, credentials, max depth, timeout, and no public Browser exposure.
- **Validation:** container/schema smoke test where Docker is available; projection idempotency and traversal tests.
- **Evidence:** record container and test output; if Docker unavailable, record alternative contract evidence.

### P06 — Typed T01–T23 registry

- **Status:** `PLANNED`
- **Dependencies:** `P04`, `P03`
- **Owner scope:** registry schemas, dispatch, authorization/audit metadata
- **Tasks:** implement all 23 Pydantic input/output contracts; create registry manifest; validate limits, allowed values, scope, and timeout; dispatch each tool to its owner engine/reasoning stage; reject unknown/public direct tool routes.
- **Files:** `src/registry/schemas.py`, `src/registry/tools.py`, `src/registry/dispatch.py`, `src/registry/manifest.py`, `tests/unit/registry/`.
- **Acceptance criteria:** exactly T01–T23 are present; each tool has typed input/output, owner, authorization requirement, citation/provenance requirement, and audit action; planner plans can reference tools but cannot emit unrestricted SQL/Cypher.
- **Review gate:** compare every tool and engine mapping against `.LOCK/AGENTS.md`; confirm T15 is deterministic lead ranking and T20/T22 evidence-related, not autonomous decision-making.
- **Validation:** registry completeness assertion; schema boundary tests; unauthorized/over-limit dispatch tests.
- **Evidence:** record exact tool IDs and passing test output.

### P07 — Deterministic SQL and hybrid search engines

- **Status:** `PLANNED`
- **Dependencies:** `P04`, `P06`, `P03`
- **Owner scope:** T01/T02/T13 and retrieval primitives
- **Tasks:** implement permission-aware structured FIR retrieval; local vector adapter contract for 1024-d embeddings; keyword/BM25-compatible retrieval boundary; RRF `k=60`; candidate reranking boundary; citation annotations.
- **Files:** `src/engines/sql_retrieval.py`, `src/engines/search_ranking.py`, `src/engines/retrieval/`, `src/shared/embedding.py`, `tests/unit/engines/test_sql_retrieval.py`, `tests/unit/engines/test_search_ranking.py`.
- **Acceptance criteria:** exact filters/counts/dates run without LLM; hybrid results preserve source type, rank, score, and citation; top candidate limits are enforced; unavailable pgvector degrades explicitly to local deterministic search.
- **Review gate:** validate Catalyst/ZCQL capabilities before using SQL syntax from the logical reference; check vector dimensions and HNSW settings as deploy-time validation items.
- **Validation:** deterministic fixture queries; RRF/reranker tests; citation coverage assertions.
- **Evidence:** record precision inputs only if measured; otherwise record functional evidence without benchmark claims.

### P08 — Fast-path execution and evidence gate

- **Status:** `PLANNED`
- **Dependencies:** `P06`, `P07`
- **Owner scope:** fast routing, T20 evidence/explainability, cited responses
- **Tasks:** classify exact/structured low-risk requests; execute one deterministic engine; validate claims, numbers, permissions, citations, contradictions, uncertainty, and audit metadata; return synchronous cited response.
- **Files:** `src/orchestration/router.py`, `src/engines/evidence.py`, `src/orchestration/fast_path.py`, `src/domain/evidence.py`, `tests/unit/orchestration/test_fast_path.py`, `tests/unit/engines/test_evidence.py`.
- **Acceptance criteria:** exact lookup/count/path/date queries do not call an LLM; every released claim has resolvable provenance; missing/contradicting evidence is surfaced; restricted results are filtered.
- **Review gate:** verify mandatory gate semantics, no private chain-of-thought, and source coverage against `.LOCK/ai-architecture.md` and `.LOCK/AGENTS.md`.
- **Validation:** tests for supported, unsupported, contradictory, unauthorized, and no-result queries; minimal CLI smoke test.
- **Evidence:** record test output and representative structured response.

### P09 — Persistent investigation state and checkpointing

- **Status:** `PLANNED`
- **Dependencies:** `P04`, `P03`, `P08`
- **Owner scope:** investigation lifecycle, case memory, evidence board, timeline, hypotheses, leads
- **Tasks:** implement investigation CRUD/domain service; Catalyst-compatible checkpoint interface with local adapter; persist state versions; implement evidence pinning, notes, hypotheses, timeline entries, lead status, and graph view state; implement deterministic **Investigation Health** aggregation for evidence coverage, timeline completeness, network coverage, financial coverage, witness coverage, contradictions, and missing critical evidence.
- **Files:** `src/domain/investigation_state.py`, `src/services/investigations.py`, `src/services/checkpoints.py`, `src/services/evidence_board.py`, `src/services/hypotheses.py`, `src/services/leads.py`, `src/services/investigation_health.py`, `tests/unit/services/`.
- **Acceptance criteria:** Created/Active/Suspended/Closed/Archived transitions are validated; state resumes across local process instances; pinning an item updates connected state; Investigation Health exposes deterministic coverage percentages, contradiction count, and missing critical evidence with provenance; every mutation is authorized and auditable.
- **Review gate:** compare state to database schema, `InvestigationState` in AGENTS, and workspace synchronization rules; no state is kept only in conversation memory.
- **Validation:** lifecycle tests; checkpoint round-trip; evidence/hypothesis/lead synchronization tests.
- **Evidence:** record test output and serialized state assertion.

### P10 — Capability/resource REST and SSE APIs

- **Status:** `PLANNED`
- **Dependencies:** `P08`, `P09`, `P06`
- **Owner scope:** Python API/BFF adapters and stream protocol
- **Tasks:** implement investigation run lifecycle, capability routes, resource routes, SSE event schema, cookie/bearer auth handling, multipart upload boundary, standardized errors, and request audit context.
- **Files:** `functions/api/investigation_runs.py`, `functions/api/capability_api.py`, `functions/api/resource_api.py`, `functions/api/sse_api.py`, `functions/api/upload_api.py`, `src/api/`, `tests/integration/api/`.
- **Acceptance criteria:** complex runs are created by REST and streamed by SSE; simple lookups may return synchronously; event types include plan/tool/evidence/token/citation/error/done as applicable; tools are never public routes.
- **Review gate:** verify path versioning `/api/v1`, API timeout target `30s`, SSE authentication behavior, CORS boundary, and no native EventSource Authorization-header assumption.
- **Validation:** local API smoke test; SSE event-contract test; multipart rejection/size-limit tests.
- **Evidence:** record HTTP/SSE output and test results.

### P11 — Next.js investigation workspace with Feature-Sliced Design

- **Status:** `PLANNED`
- **Dependencies:** `P09`, `P10`
- **Owner scope:** Next.js 15 App Router + React 19 + TypeScript workspace shell and FSD slices
- **Tasks:** create Catalyst AppSail-compatible Next.js client; implement `client/src/app`, `features`, `entities`, `widgets`, `shared`, and `styles`; add Tailwind CSS v4, shadcn/ui, Radix UI, Lucide React, Motion, TanStack Query v5, Zustand, React Hook Form, Zod, TanStack Table, Cytoscape.js, Apache ECharts, MapLibre GL, react-resizable-panels, cmdk, Sonner, React DnD, react-markdown, React PDF, and next-themes; implement seven synchronized panels; add REST/JWT/Catalyst Auth and SSE clients; add card renderer shell; implement responsive states, confidence, stale indicators, and Investigation Health.
- **Files:** `client/package.json`, `client/next.config.ts`, `client/tsconfig.json`, `client/postcss.config.mjs`, `client/src/app/`, `client/src/features/`, `client/src/entities/`, `client/src/widgets/`, `client/src/shared/`, `client/src/styles/`, `docs/frontend-architecture.md`, `tests/e2e/workspace/`.
- **Acceptance criteria:** workspace is investigation-first, not chat-first; all seven panels render from one investigation state; pin/evidence/timeline/graph/leads/hypothesis/card changes synchronize; proactive alerts appear before query input; FSD dependency direction is enforced; no real data is bundled.
- **Review gate:** compare panels and interactions to `.LOCK/investigation-workspace.md`; compare card rendering/lifecycle to `.LOCK/intelligence-cards.md`; verify Next.js App Router/React 19/FSD and the requested UI/data/visualization stack; verify Catalyst AppSail deployment does not alter backend contracts.
- **Validation:** `uv` is used for backend checks; frontend Node checks are run from `client/` using the pinned package-manager workflow; typecheck/lint/build; browser smoke test or documented headless alternative; state synchronization tests.
- **Evidence:** record build and test output, not visual claims without a runnable check.

### P12 — Deep-path orchestrator and reasoning stages

- **Status:** `PLANNED`
- **Dependencies:** `P06`, `P08`, `P09`, `P10`
- **Owner scope:** LangGraph state machine, Planner/Reasoner/Reporter boundaries
- **Tasks:** implement `InvestigationState`; deterministic route; optional validated Planner; bounded parallel engine fan-out/fan-in; reconciliation; Reasoner and Reporter LiteLLM interfaces; checkpoints; SSE progress; graceful degradation.
- **Files:** `src/orchestration/orchestrator.py`, `src/orchestration/planner_stage.py`, `src/orchestration/reasoner_stage.py`, `src/orchestration/reporter_stage.py`, `src/orchestration/reconciliation.py`, `tests/unit/orchestration/`, `tests/integration/orchestration/`.
- **Acceptance criteria:** deep queries follow Planner → engines → gate/reconciliation → Reasoner → deterministic lead ranking → optional Reporter; planner cannot emit unrestricted queries; engine calls are bounded and parallel only when independent; LLM provider is selected through LiteLLM fallback chain.
- **Review gate:** confirm orchestrator is not an agent; only three LLM stages exist; evidence gate runs before release; actual concurrency/latency is measured rather than claimed.
- **Validation:** fake-provider orchestration tests; failure/degradation tests; checkpoint/resume; SSE event sequence assertions.
- **Evidence:** record trace output, provider fallback tests, and no-LLM fast-path test.

### P13 — Remaining deterministic intelligence engines

- **Status:** `PLANNED`
- **Dependencies:** `P05`, `P07`, `P12`
- **Owner scope:** graph, pattern, behavioral, financial, forecasting, timeline, lead ranking
- **Tasks:** implement bounded graph traversal/community/centrality/path tools; MO and temporal pattern analysis; behavioral profile features; financial flow/layering indicators; hotspot/forecast signals with uncertainty; timeline reconstruction; deterministic lead ranking.
- **Files:** `src/engines/graph_intelligence.py`, `pattern_analysis.py`, `behavioral_profiling.py`, `financial_analysis.py`, `forecasting.py`, `timeline.py`, `lead_ranking.py`, `tests/unit/engines/`.
- **Acceptance criteria:** each engine returns typed facts/signals with source evidence, parameters, computation metadata, and uncertainty; no engine declares guilt, legal sufficiency, or guaranteed future conduct; lead ranking is deterministic and review-oriented.
- **Review gate:** compare outputs to domain/workflow/engine docs; verify no LLM computes totals, paths, dates, scores, or forecasts; validate bounded depth/hops/candidate counts.
- **Validation:** synthetic scenario fixtures; deterministic repeatability; edge cases for empty/contradictory/partial data.
- **Evidence:** record test output and sample provenance packages.

### P14 — Intelligence card materialization and lifecycle

- **Status:** `PLANNED`
- **Dependencies:** `P09`, `P13`, `P08`
- **Owner scope:** 15 cards, storage tiers, versioning, freshness, rendering contracts
- **Tasks:** implement typed schemas for all 15 cards; metadata index; canonical Stratus/local object storage; cache adapter; version/supersession; stale/refresh/archive transitions; card-to-evidence provenance.
- **Files:** `src/domain/cards.py`, `src/services/cards.py`, `src/adapters/card_store.py`, `client/src/features/intelligence/`, `client/src/widgets/`, `tests/unit/cards/`, `tests/integration/cards/`.
- **Acceptance criteria:** all 15 card types validate required fields, confidence, provenance, timestamps, freshness, and human-review markers; storage flow is canonical JSON → metadata index → hot cache; historical versions remain retrievable.
- **Review gate:** compare schemas/freshness/lifecycle to `.LOCK/intelligence-cards.md` and table constraints; distinguish card types in the logical schema from the 15 product cards without data loss.
- **Validation:** schema/lifecycle tests; stale/refresh/archive tests; card rendering smoke test.
- **Evidence:** record card completeness and lifecycle test results.

### P15 — Signals, proactive alerts, and entity resolution

- **Status:** `PLANNED`
- **Dependencies:** `P05`, `P09`, `P13`, `P14`, `P10`
- **Owner scope:** ingestion events, matching, alert delivery, merge review
- **Tasks:** implement idempotent FIR ingestion pipeline; entity normalization/resolution as a first-class subsystem; human approval for Person merges; exact auto-merge only for locked identifier types; active-investigation matching; proactive-first workspace feed showing new linked FIRs before query input; alert cards and SSE delivery; card invalidation.
- **Files:** `functions/signals/`, `src/services/entity_resolution.py`, `src/services/proactive_alerts.py`, `src/engines/search_ranking.py`, `tests/integration/signals/`, `tests/unit/entity_resolution/`.
- **Acceptance criteria:** synthetic new FIR can produce entity/graph/card updates idempotently; matching active investigations generates authorized alerts; person merges require explicit officer approval; alerts expire according to card policy.
- **Review gate:** compare Signal flow to architecture/workspace/scenarios; verify no broad broadcast, no silent merge, no ungrounded alert, and delivery lag is measured.
- **Validation:** replay/idempotency tests; approval/rejection tests; alert authorization and SSE tests.
- **Evidence:** record event trace and timing measurements where available.

### P16 — RBAC, masking, immutable audit, and governance hardening

- **Status:** `PLANNED`
- **Dependencies:** `P03`, `P06`, `P09`, `P10`, `P15`
- **Owner scope:** authorization, scope filtering, PII masking, hash-chain audit
- **Tasks:** implement SHO/IO/DCP/Analyst/SP policies; station/district/case scope; analyst masking; permission checks before each tool and card; SHA-512/hash-chain audit records; audit verification; secure export classification.
- **Files:** `src/shared/auth.py`, `src/shared/permissions.py`, `src/shared/masking.py`, `src/services/audit.py`, `functions/signals/audit_logger.py`, `tests/unit/security/`, `tests/integration/security/`.
- **Acceptance criteria:** role matrix is enforced on reads, mutations, cards, alerts, exports, and reports; cross-scope PII is masked; audit entries are tamper-evident and verifiable; consequential outputs contain human-review qualification.
- **Review gate:** compare exactly to architecture/ontology RBAC and audit rules; verify secrets, logs, error responses, and exports do not leak PII; do not claim legal admissibility.
- **Validation:** authorization matrix tests; hash-chain tamper test; secret-scan; dependency/security checks available in repo.
- **Evidence:** record role-by-operation matrix output and audit verification.

### P17 — Multilingual, voice, document, and report boundaries

- **Status:** `PLANNED`
- **Dependencies:** `P10`, `P12`, `P14`, `P16`
- **Owner scope:** IndicTrans2, Faster-Whisper, Piper/Edge TTS, Tesseract, report output
- **Tasks:** add optional model adapters; multipart upload validation; Kannada/English translation preserving entities; OCR pipeline; report generation from evidence-gated package; fallback/pre-recorded demo assets.
- **Files:** `src/adapters/onnx/`, `src/services/voice.py`, `src/services/ocr.py`, `src/services/reports.py`, `functions/api/upload_api.py`, `tests/unit/media/`, `tests/integration/reports/`.
- **Acceptance criteria:** features are optional and fail safely when models are absent; proper nouns can be preserved; reports contain citations/classification/human-review language; no upload bypasses authorization or size/type limits.
- **Review gate:** verify model names, local CPU boundary, memory constraints, no external secret leakage, and no legal/custody claims from generated reports.
- **Validation:** synthetic English/Kannada fixture tests; report citation test; upload security tests; model smoke tests only when model assets are present.
- **Evidence:** record available and unavailable validation paths explicitly.

### P18 — Ten scenario integration suite and demo wiring

- **Status:** `PLANNED`
- **Dependencies:** `P11`, `P12`, `P13`, `P14`, `P15`, `P16`, `P17`
- **Owner scope:** end-to-end synthetic scenarios and demo fixtures
- **Tasks:** implement all ten scenario fixtures as CI integration tests; verify primary six demo order; wire workspace artifacts, proactive alerts, hypotheses, handover, and strategic briefing; add deterministic fallback fixtures for provider outages.
- **Files:** `data/scenarios/`, `tests/integration/scenarios/`, `docs/demo-script.md`, `scripts/seed_demo.py`, `scripts/smoke_demo.py`.
- **Acceptance criteria:** each scenario exercises the documented route and relevant engines/cards; all ten use synthetic data; workspace panels synchronize; proactive scenarios are system-initiated; every output is cited/qualified; no scenario asserts unmeasured illustrative numbers as achieved performance.
- **Review gate:** compare each test to `.LOCK/investigation-scenarios.md`, requirements matrix, demo order, and RBAC persona; verify no scenario changes locked scope.
- **Validation:** `pytest` scenario suite; local API/UI smoke; deterministic replay; failure fallback tests.
- **Evidence:** record per-scenario pass/fail and artifact assertions.

### P19 — Performance, quality, capacity, and resilience evaluation

- **Status:** `PLANNED`
- **Dependencies:** `P18`
- **Owner scope:** benchmark harness, load tests, quality metrics, failure modes
- **Tasks:** measure p50/p95/p99 latency, first token/SSE timing, query throughput, cache behavior, vector/graph performance, citation coverage, unsupported claims, Precision@K/Recall@K where labels exist, entity-resolution quality, language parity, token/cost usage; run capacity tests against synthetic scale targets.
- **Files:** `benchmarks/`, `tests/performance/`, `tests/load/`, `docs/benchmarks.md`, `scripts/benchmark.py`.
- **Acceptance criteria:** results are reproducible and labeled as measurements; unmeasured design targets remain explicitly pending; degraded dependencies produce bounded behavior; no capacity claim exceeds tested environment.
- **Review gate:** compare measured results with every architecture target; document Catalyst/AppSail limitations, memory/port/timeouts, and any required scope reduction.
- **Validation:** benchmark and load commands; report generation; `git diff --check`.
- **Evidence:** store machine-readable result paths and summarized measured values.

### P20 — Final architecture, security, and demo review

- **Status:** `PLANNED`
- **Dependencies:** `P19`
- **Owner scope:** release readiness and final evidence
- **Tasks:** run complete unit/integration/e2e suite; inspect schema/ontology/tool/workflow/card/workspace alignment; verify environment and connection configuration; scan secrets/private files; validate deployment manifests; update this plan with final evidence and known limitations.
- **Files:** `README.md`, `docs/setup.md`, `docs/api-reference.md`, `docs/operations.md`, `docs/limitations.md`, `implementation_phases.md`.
- **Acceptance criteria:** all required tests pass or have documented blockers; all phase review gates are complete; no locked file or private file was modified; final demo runs on synthetic data; claims are qualified by evidence.
- **Review gate:** final checklist in Section 3 is complete for every phase; architecture lock confirmation is unchanged; no direct agent database path, public registry route, unsupported legal claim, or hidden secret remains.
- **Validation:** full test/type/lint/build/smoke/benchmark suite; `git status --short --ignored`; `git diff --check`; secret and private-file checks.
- **Evidence:** record final command outputs, artifact paths, measured benchmarks, and unresolved limitations.

## 5. Phase Review Record

This section is updated only after concrete work and validation. Do not mark a phase complete based on intent or code existence alone.

### Review record: P01 — Repository and environment baseline

- **Status:** `COMPLETE`
- **Started:** 2026-07-25T18:17:33Z
- **Completed:** 2026-07-25T18:22:02Z
- **Implementation evidence:** Created `README.md`, `pyproject.toml`, `uv.lock`, `docs/setup.md`, `docs/investigator-journey.md`, standard-library smoke tests, and explicit repository boundary placeholders under `src/`, `functions/`, `client/`, `data/`, and `appsail/`. The journey is explicitly derived from locked workspace/workflow/scenario documents and puts proactive alerts, evidence, hypotheses, Investigation Health, human ownership, and closure in the investigator flow.
- **Validation evidence:** `uv 0.11.25`; `uv run python --version` returned `Python 3.11.15`; `uv run python -m unittest discover -s tests -p 'test_*.py' -v` ran 4 tests with `OK`; `uv run python -m compileall -q tests` passed; executable contract assertions passed; `git diff --check` passed.
- **Review-gate evidence:** `pyproject.toml` records Python-only backend, Python 3.11 deployment, synthetic-only data, REST/SSE/multipart protocols, ports 7687/7474, and 30/60/300-second timeout values. `.LOCK/TODO.md` and `session-ses_0754.md` remain ignored; `.LOCK/TODO.md` has no diff. No external service or secret was added.
- **Known blockers:** Local `pytest` is unavailable, so Phase 1 uses the standard-library `unittest` runner through `uv`; framework-specific tests are deferred to later phases.

### Review records: P02–P20

- **Status:** `PLANNED`
- **Evidence:** not started
