# KSP InvestigateAI Implementation Phases

> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: `.LOCK/DECISIONS.md` (2026-07-24)
> Knowledge base: `.LOCK/*.md`, ingested in the user-mandated order
> Plan version: 1.0.0
> Last reviewed: 2026-07-24
> Current phase: `P18`
> Current state: `COMPLETE`

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
- Hexel Studio owns production agent runtime and orchestration. Until it is available, `LocalRunner` is temporary infrastructure that only invokes agents, passes `InvestigationState`, and returns results; it must not become a local orchestration platform.
- Only Planner, Reasoner, and Reporter are LLM-powered reasoning stages.
- Agents/reasoning stages never access databases directly; all access goes through authorized typed T01–T23 tools and deterministic engines.
- Facts, counts, paths, scores, dates, totals, and forecasts come from deterministic engines. LLM output is grounded communication or structured reasoning over validated results.
- Every proposed feature must answer: **is this investigation intelligence or infrastructure?** Build investigation intelligence; integrate with Catalyst/Hexel infrastructure instead of rebuilding it.
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
- `.LOCK/` remains authoritative architecture/domain documentation. Its non-private Markdown may be updated only by an explicitly authorized architecture amendment; implementation phases must not change it implicitly. `.LOCK/TODO.md` and ignored session files remain untouched.

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

1. **Locked alignment:** `.LOCK/DECISIONS.md`, `.LOCK/architecture.md`, `.LOCK/ai-architecture.md`, and `.LOCK/AGENTS.md` remain authoritative; any explicitly authorized runtime amendment is recorded consistently across the non-private source documents.
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

- **Status:** `COMPLETE`
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

- **Status:** `COMPLETE`
- **Dependencies:** `P02`
- **Owner scope:** Catalyst Data Store, Cache, Stratus, Signals, Cron, Circuits, Auth boundaries
- **Tasks:** define typed ports/interfaces; implement local in-memory/file adapters for development; add Catalyst adapter stubs with validated request/response shapes; implement Neo4j client boundary with Bolt port `7687`; add LiteLLM model-router boundary.
- **Files:** `src/shared/ports.py`, `src/adapters/catalyst/`, `src/adapters/neo4j.py`, `src/adapters/llm.py`, `src/adapters/cache.py`, `src/adapters/stratus.py`, `functions/shared/` thin wrappers, `tests/unit/adapters/`.
- **Acceptance criteria:** engines depend on interfaces rather than vendor SDKs; local tests run without Catalyst/Neo4j/LLM credentials; external calls are disabled unless explicitly configured.
- **Review gate:** confirm REST/SSE/multipart are the only initial external protocols; no direct database access from agents; connection strings and TLS/auth settings are centralized.
- **Validation:** adapter contract tests; config smoke test; no-network default test.
- **Evidence:** record outputs and any Catalyst compatibility limitations.

### P04 — Logical data contracts and synthetic fixtures

- **Status:** `COMPLETE`
- **Dependencies:** `P02`, `P03`
- **Owner scope:** domain models, schema mapping, synthetic data
- **Tasks:** model FIRs, entities, FIR-entity links, relationships, investigations, evidence, timeline, engine runs, provenance, cards, and audit records; implement Karnataka/CCTNS identifiers and IPC/BNS mappings; create deterministic synthetic fixture generators; document logical-to-Catalyst mapping gaps.
- **Files:** `src/domain/models.py`, `src/domain/enums.py`, `src/domain/ontology.py`, `src/domain/schema_mapping.py`, `data/generator/`, `data/seed/`, `tests/unit/domain/`, `docs/data-contracts.md`.
- **Acceptance criteria:** models enforce locked status/role/type values and confidence bounds; fixtures contain no real sensitive data; generated FIR numbers and station codes follow locked formats; every relationship can carry evidence/provenance.
- **Review gate:** compare model fields to `.LOCK/database-schema.md`, `.LOCK/ontology.md`, and `.LOCK/crime-domain.md`; explicitly flag non-portable PostgreSQL constructs rather than silently using them.
- **Validation:** model validation tests; fixture reproducibility test; schema assertion script.
- **Evidence:** record generated counts, checksums, and assertion output.

### P05 — Neo4j projection and graph schema

- **Status:** `COMPLETE`
- **Dependencies:** `P04`
- **Owner scope:** graph projection, constraints, indexes, local AppSail container
- **Tasks:** implement idempotent Catalyst-authoritative-to-Neo4j projection; add labels, relationship properties, constraints, indexes, bounded traversal helpers; add AppSail Docker configuration with port `7687`, production HTTP restriction, memory settings, health check, and backup/export boundary.
- **Files:** `appsail/neo4j/Dockerfile`, `appsail/neo4j/neo4j.conf`, `appsail/neo4j/import/schema.cypher`, `appsail/neo4j/scripts/`, `src/engines/graph_intelligence.py`, `tests/integration/graph/`.
- **Acceptance criteria:** synthetic entities/FIRs project idempotently; required relationship evidence and verification properties survive projection; bounded traversal/path queries return citations; health check detects unavailable graph.
- **Review gate:** validate labels and relationship types against ontology/schema; check Bolt URI/port, credentials, max depth, timeout, and no public Browser exposure.
- **Validation:** container/schema smoke test where Docker is available; projection idempotency and traversal tests.
- **Evidence:** record container and test output; if Docker unavailable, record alternative contract evidence.

### P06 — Typed T01–T23 registry

- **Status:** `COMPLETE`
- **Dependencies:** `P04`, `P03`
- **Owner scope:** registry schemas, dispatch, authorization/audit metadata
- **Tasks:** implement all 23 Pydantic input/output contracts; create registry manifest; validate limits, allowed values, scope, and timeout; dispatch each tool to its owner engine/reasoning stage; reject unknown/public direct tool routes.
- **Files:** `src/registry/schemas.py`, `src/registry/tools.py`, `src/registry/dispatch.py`, `src/registry/manifest.py`, `tests/unit/registry/`.
- **Acceptance criteria:** exactly T01–T23 are present; each tool has typed input/output, owner, authorization requirement, citation/provenance requirement, and audit action; planner plans can reference tools but cannot emit unrestricted SQL/Cypher.
- **Review gate:** compare every tool and engine mapping against `.LOCK/AGENTS.md`; confirm T15 is deterministic lead ranking and T20/T22 evidence-related, not autonomous decision-making.
- **Validation:** registry completeness assertion; schema boundary tests; unauthorized/over-limit dispatch tests.
- **Evidence:** record exact tool IDs and passing test output.

### P07 — Deterministic SQL and hybrid search engines

- **Status:** `COMPLETE`
- **Dependencies:** `P04`, `P06`, `P03`
- **Owner scope:** T01/T02/T13 and retrieval primitives
- **Tasks:** implement permission-aware structured FIR retrieval; local vector adapter contract for 1024-d embeddings; keyword/BM25-compatible retrieval boundary; RRF `k=60`; candidate reranking boundary; citation annotations.
- **Files:** `src/engines/sql_retrieval.py`, `src/engines/search_ranking.py`, `src/engines/retrieval/`, `src/shared/embedding.py`, `tests/unit/engines/test_sql_retrieval.py`, `tests/unit/engines/test_search_ranking.py`.
- **Acceptance criteria:** exact filters/counts/dates run without LLM; hybrid results preserve source type, rank, score, and citation; top candidate limits are enforced; unavailable pgvector degrades explicitly to local deterministic search.
- **Review gate:** validate Catalyst/ZCQL capabilities before using SQL syntax from the logical reference; check vector dimensions and HNSW settings as deploy-time validation items.
- **Validation:** deterministic fixture queries; RRF/reranker tests; citation coverage assertions.
- **Evidence:** record precision inputs only if measured; otherwise record functional evidence without benchmark claims.

### P08 — Fast-path execution and evidence gate

- **Status:** `COMPLETE`
- **Dependencies:** `P06`, `P07`
- **Owner scope:** fast routing, T20 evidence/explainability, cited responses
- **Tasks:** classify exact/structured low-risk requests; execute one deterministic engine; validate claims, numbers, permissions, citations, contradictions, uncertainty, and audit metadata; return synchronous cited response.
- **Files:** `src/orchestration/router.py`, `src/engines/evidence.py`, `src/orchestration/fast_path.py`, `src/domain/evidence.py`, `tests/unit/orchestration/test_fast_path.py`, `tests/unit/engines/test_evidence.py`.
- **Acceptance criteria:** exact lookup/count/path/date queries do not call an LLM; every released claim has resolvable provenance; missing/contradicting evidence is surfaced; restricted results are filtered.
- **Review gate:** verify mandatory gate semantics, no private chain-of-thought, and source coverage against `.LOCK/ai-architecture.md` and `.LOCK/AGENTS.md`.
- **Validation:** tests for supported, unsupported, contradictory, unauthorized, and no-result queries; minimal CLI smoke test.
- **Evidence:** record test output and representative structured response.

### P09 — Persistent investigation state and checkpointing

- **Status:** `COMPLETE`
- **Dependencies:** `P04`, `P03`, `P08`
- **Owner scope:** investigation lifecycle, case memory, evidence board, timeline, hypotheses, leads
- **Tasks:** implement investigation CRUD/domain service; Catalyst-compatible checkpoint interface with local adapter; persist state versions; implement evidence pinning, notes, hypotheses, timeline entries, lead status, and graph view state; implement deterministic **Investigation Health** aggregation for evidence coverage, timeline completeness, network coverage, financial coverage, witness coverage, contradictions, and missing critical evidence.
- **Files:** `src/domain/investigation_state.py`, `src/services/investigations.py`, `src/services/checkpoints.py`, `src/services/evidence_board.py`, `src/services/hypotheses.py`, `src/services/leads.py`, `src/services/investigation_health.py`, `tests/unit/services/`.
- **Acceptance criteria:** Created/Active/Suspended/Closed/Archived transitions are validated; state resumes across local process instances; pinning an item updates connected state; Investigation Health exposes deterministic coverage percentages, contradiction count, and missing critical evidence with provenance; every mutation is authorized and auditable.
- **Review gate:** compare state to database schema, `InvestigationState` in AGENTS, and workspace synchronization rules; no state is kept only in conversation memory.
- **Validation:** lifecycle tests; checkpoint round-trip; evidence/hypothesis/lead synchronization tests.
- **Evidence:** record test output and serialized state assertion.

### P10 — Capability/resource REST and SSE APIs

- **Status:** `COMPLETE`
- **Dependencies:** `P08`, `P09`, `P06`
- **Owner scope:** Python API/BFF adapters and stream protocol
- **Tasks:** implement investigation run lifecycle, capability routes, resource routes, SSE event schema, cookie/bearer auth handling, multipart upload boundary, standardized errors, and request audit context; communicate with the investigation service and Runner protocol without depending on LocalRunner or HexelRunner.
- **Files:** `functions/api/investigation_runs.py`, `functions/api/capability_api.py`, `functions/api/resource_api.py`, `functions/api/sse_api.py`, `functions/api/upload_api.py`, `src/api/`, `tests/integration/api/`.
- **Acceptance criteria:** complex runs are created by REST and streamed by SSE; simple lookups may return synchronously through the P08 fast path; event types include plan/tool/evidence/token/citation/error/done as applicable; tools are never public routes; API code depends on the Runner protocol rather than LocalRunner or HexelRunner.
- **Review gate:** verify path versioning `/api/v1`, API timeout target `30s`, SSE authentication behavior, CORS boundary, and no native EventSource Authorization-header assumption.
- **Validation:** local API smoke test; SSE event-contract test; multipart rejection/size-limit tests.
- **Evidence:** record HTTP/SSE output and test results.

### P11 — Next.js investigation workspace with Feature-Sliced Design

- **Status:** `COMPLETE`
- **Dependencies:** `P09`, `P10`
- **Owner scope:** Next.js 15 App Router + React 19 + TypeScript workspace shell and FSD slices
- **Tasks:** create Catalyst AppSail-compatible Next.js client; implement `client/src/app`, `features`, `entities`, `widgets`, `shared`, and `styles`; add Tailwind CSS v4, shadcn/ui, Radix UI, Lucide React, Motion, TanStack Query v5, Zustand, React Hook Form, Zod, TanStack Table, Cytoscape.js, Apache ECharts, MapLibre GL, react-resizable-panels, cmdk, Sonner, React DnD, react-markdown, React PDF, and next-themes; implement seven synchronized panels; add REST/JWT/Catalyst Auth and SSE clients; add card renderer shell; implement responsive states, confidence, stale indicators, and Investigation Health.
- **Files:** `client/package.json`, `client/next.config.ts`, `client/tsconfig.json`, `client/postcss.config.mjs`, `client/src/app/`, `client/src/features/`, `client/src/entities/`, `client/src/widgets/`, `client/src/shared/`, `client/src/styles/`, `docs/frontend-architecture.md`, `tests/e2e/workspace/`.
- **Acceptance criteria:** workspace is investigation-first, not chat-first; all seven panels render from one investigation state; pin/evidence/timeline/graph/leads/hypothesis/card changes synchronize; proactive alerts appear before query input; FSD dependency direction is enforced; no real data is bundled.
- **Review gate:** compare panels and interactions to `.LOCK/investigation-workspace.md`; compare card rendering/lifecycle to `.LOCK/intelligence-cards.md`; verify Next.js App Router/React 19/FSD and the requested UI/data/visualization stack; verify Catalyst AppSail deployment does not alter backend contracts.
- **Validation:** `uv` is used for backend checks; frontend Node checks are run from `client/` using the pinned package-manager workflow; typecheck/lint/build; browser smoke test or documented headless alternative; state synchronization tests.
- **Evidence:** record build and test output, not visual claims without a runnable check.

### P12 — Temporary Runner and Strands agent fleet

- **Status:** `COMPLETE`
- **Dependencies:** `P06`, `P08`, `P09`, `P10`
- **Owner scope:** minimal LocalRunner interface and reusable Strands agents; Hexel is the future runtime owner
- **Tasks:** define a small `Runner.run(state: InvestigationState) -> InvestigationState` interface; implement `LocalRunner` that invokes agents and passes updated state; define the future Hexel adapter boundary; define one `AgentContext` containing `state`, `auth_context`, `registry`, `llm`, and `logger`; implement Planner, Evidence, Graph Intelligence, Pattern Intelligence, Financial Intelligence, Timeline, Reasoner, and Reporter agent interfaces using Strands; keep agent business logic outside the runner; preserve existing registry, adapter, evidence, and engine boundaries.
- **Files:** `docs/orchestration-architecture.md`, `src/orchestration/runner.py`, `src/orchestration/local_runner.py`, `src/orchestration/hexel_runner.py`, `src/orchestration/state.py`, `src/agents/`, `tests/unit/orchestration/`, `tests/integration/orchestration/`.
- **Acceptance criteria:** LocalRunner only invokes agents, passes shared state, and returns final state; it does not schedule, retry, persist, stream, distribute, or implement workflow graphs; each agent accepts `AgentContext` and returns updated `InvestigationState`, does not orchestrate other agents, does not access Catalyst/Neo4j/providers directly, and requires no Hexel dependency; replacing LocalRunner with Hexel integration does not change agents, tools, APIs, domain models, or frontend.
- **Review gate:** confirm KSP is not recreating Hexel capabilities, an external graph/orchestration framework, gateway/platform services, a policy platform, a workflow engine, or a skill platform; confirm Catalyst remains infrastructure and Neo4j remains a projection/query store; confirm no T01–T23 or business-domain redesign.
- **Validation:** fake-agent LocalRunner sequential state-passing test; agent interface tests; runner substitution contract test without Hexel; no-direct-database/provider imports; regression tests for P08 fast path.
- **Evidence:** record state trace, agent invocation order, final state, substitution contract, and no-platform-rebuild assertions.

### P13 — Deterministic intelligence engines and agent business capabilities

- **Status:** `COMPLETE`
- **Dependencies:** `P05`, `P07`, `P12`
- **Owner scope:** graph, pattern, behavioral, financial, forecasting, timeline, lead-ranking engines and their Strands agent business logic
- **Tasks:** implement bounded graph traversal/community/centrality/path tools; MO and temporal pattern analysis; behavioral profile features; financial flow/layering indicators; hotspot/forecast signals with uncertainty; timeline reconstruction; deterministic lead ranking; connect the corresponding Strands agents to validated engine/tool outputs without creating a local skill/orchestration platform.
- **Files:** `src/engines/graph_intelligence.py`, `pattern_analysis.py`, `behavioral_profiling.py`, `financial_analysis.py`, `forecasting.py`, `timeline.py`, `lead_ranking.py`, `src/agents/`, `tests/unit/engines/`, `tests/unit/agents/`.
- **Acceptance criteria:** each engine returns typed facts/signals with source evidence, parameters, computation metadata, and uncertainty; agents only interpret validated results; no engine or agent declares guilt, legal sufficiency, or guaranteed future conduct; lead ranking is deterministic and review-oriented.
- **Review gate:** compare outputs to domain/workflow/engine docs; verify no LLM computes totals, paths, dates, scores, or forecasts; validate bounded depth/hops/candidate counts and no platform recreation.
- **Validation:** synthetic scenario fixtures; deterministic repeatability; agent contract tests; edge cases for empty/contradictory/partial data.
- **Evidence:** record engine outputs, agent state traces, and sample provenance packages.

### P14 — Intelligence card materialization and lifecycle

- **Status:** `COMPLETE`
- **Dependencies:** `P09`, `P13`, `P08`
- **Owner scope:** 15 cards, storage tiers, versioning, freshness, rendering contracts
- **Tasks:** implement typed schemas for all 15 cards; metadata index; canonical Stratus/local object storage; cache adapter; version/supersession; stale/refresh/archive transitions; card-to-evidence provenance.
- **Files:** `src/domain/cards.py`, `src/services/cards.py`, `src/adapters/card_store.py`, `client/src/features/intelligence/`, `client/src/widgets/`, `tests/unit/cards/`, `tests/integration/cards/`.
- **Acceptance criteria:** all 15 card types validate required fields, confidence, provenance, timestamps, freshness, and human-review markers; storage flow is canonical JSON → metadata index → hot cache; historical versions remain retrievable.
- **Review gate:** compare schemas/freshness/lifecycle to `.LOCK/intelligence-cards.md` and table constraints; distinguish card types in the logical schema from the 15 product cards without data loss.
- **Validation:** schema/lifecycle tests; stale/refresh/archive tests; card rendering smoke test.
- **Evidence:** record card completeness and lifecycle test results.

### P15 — Signals, proactive alerts, and entity resolution

- **Status:** `COMPLETE`
- **Dependencies:** `P05`, `P09`, `P13`, `P14`, `P10`
- **Owner scope:** ingestion events, matching, alert delivery, merge review
- **Tasks:** implement idempotent FIR ingestion pipeline; entity normalization/resolution as a first-class subsystem; human approval for Person merges; exact auto-merge only for locked identifier types; active-investigation matching; proactive-first workspace feed showing new linked FIRs before query input; alert cards and SSE delivery; card invalidation.
- **Files:** `functions/signals/`, `src/services/entity_resolution.py`, `src/services/proactive_alerts.py`, `src/engines/search_ranking.py`, `tests/integration/signals/`, `tests/unit/entity_resolution/`.
- **Acceptance criteria:** synthetic new FIR can produce entity/graph/card updates idempotently; matching active investigations generates authorized alerts; person merges require explicit officer approval; alerts expire according to card policy.
- **Review gate:** compare Signal flow to architecture/workspace/scenarios; verify no broad broadcast, no silent merge, no ungrounded alert, and delivery lag is measured.
- **Validation:** replay/idempotency tests; approval/rejection tests; alert authorization and SSE tests.
- **Evidence:** record event trace and timing measurements where available.

### P16 — RBAC, masking, immutable audit, and governance hardening

- **Status:** `COMPLETE`
- **Dependencies:** `P03`, `P06`, `P09`, `P10`, `P15`
- **Owner scope:** application authorization integration, Catalyst/Hexel policy integration, scope filtering, PII masking, hash-chain audit
- **Tasks:** integrate SHO/IO/DCP/Analyst/SP policies without rebuilding a policy platform; enforce station/district/case scope; analyst masking; permission checks before tools, agents, cards, alerts, exports, and reports; SHA-512/hash-chain audit records; audit verification; secure export classification.
- **Files:** `src/shared/auth.py`, `src/shared/permissions.py`, `src/shared/masking.py`, `src/services/audit.py`, `functions/signals/audit_logger.py`, `tests/unit/security/`, `tests/integration/security/`.
- **Acceptance criteria:** role matrix is enforced on reads, mutations, cards, alerts, exports, and reports; cross-scope PII is masked; audit entries are tamper-evident and verifiable; consequential outputs contain human-review qualification.
- **Review gate:** compare exactly to architecture/ontology RBAC and audit rules; verify secrets, logs, error responses, and exports do not leak PII; do not claim legal admissibility.
- **Validation:** authorization matrix tests; hash-chain tamper test; secret-scan; dependency/security checks available in repo.
- **Evidence:** record role-by-operation matrix output and audit verification.

### P17 — Multilingual, voice, document, and report boundaries

- **Status:** `COMPLETE`
- **Dependencies:** `P10`, `P12`, `P14`, `P16`
- **Owner scope:** IndicTrans2, Faster-Whisper, Piper/Edge TTS, Tesseract, report output
- **Tasks:** add optional model adapters; multipart upload validation; Kannada/English translation preserving entities; OCR pipeline; report generation from evidence-gated package; fallback/pre-recorded demo assets.
- **Files:** `src/adapters/onnx/`, `src/services/voice.py`, `src/services/ocr.py`, `src/services/reports.py`, `functions/api/upload_api.py`, `tests/unit/media/`, `tests/integration/reports/`.
- **Acceptance criteria:** features are optional and fail safely when models are absent; proper nouns can be preserved; reports contain citations/classification/human-review language; no upload bypasses authorization or size/type limits.
- **Review gate:** verify model names, local CPU boundary, memory constraints, no external secret leakage, and no legal/custody claims from generated reports.
- **Validation:** synthetic English/Kannada fixture tests; report citation test; upload security tests; model smoke tests only when model assets are present.
- **Evidence:** record available and unavailable validation paths explicitly.

### P18 — Ten scenario integration suite and demo wiring

- **Status:** `COMPLETE`
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

### Review record: P02 — Python backend scaffold and configuration

- **Status:** `COMPLETE`
- **Started:** 2026-07-25T18:28:21Z
- **Completed:** 2026-07-25T18:30:39Z
- **Implementation evidence:** Added stdlib-only `src/shared/config.py`, `src/shared/errors.py`, and `src/shared/clock.py`; package boundaries for `src/shared`, `src/domain`, `src/engines`, `src/registry`, `src/orchestration`, `src/adapters`, and Catalyst function package initialization; `.env.example`; setuptools package discovery; and `tests/unit/shared/test_config.py`. `uv.lock` remains the dependency lock and no runtime service SDK was introduced.
- **Validation evidence:** `uv lock` resolved successfully; `uv run python -m unittest discover -s tests -p 'test_*.py' -v` ran 13 tests with `OK`; `uv run python -m compileall -q src functions tests` passed; P02 configuration smoke assertions passed; `git diff --check` passed.
- **Review-gate evidence:** Settings represent the locked Neo4j ports `7687`/`7474`, API/signal/job timeouts `30`/`60`/`300`, four-provider model chain, BGE-M3 1024-dimensional embeddings, Catalyst identifiers, Data Store/Cache/Stratus/Auth flags, and all four provider credential variables. Local/test mode permits deterministic execution without credentials; Catalyst/production mode requires deployment identifiers and Neo4j credentials, rejects insecure HTTPS boundaries, rejects locked-port overrides, and redacts credentials from repr/diagnostics. No secrets or private files were added; `.LOCK/TODO.md` and `session-ses_0754.md` remain ignored and unchanged.
- **Known blockers:** Formatter/linter/type checker are not configured yet; their setup is deferred to the planned tooling phase. No Catalyst compatibility claim was made.

### Review record: P03 — Catalyst integration boundaries and local adapters

- **Status:** `COMPLETE`
- **Started:** 2026-07-25T18:31:14Z
- **Completed:** 2026-07-25T18:33:52Z
- **Implementation evidence:** Added typed `src/shared/ports.py`; local Data Store, Cache, Object Store, Event Bus, and Auth adapters; disabled-by-default Catalyst service wrappers; `Neo4jClient` Bolt boundary; `LiteLLMRouter` provider-neutral boundary; cache/Stratus factories; thin `functions/shared` configuration bridge; and adapter contract tests. External SDK imports and business logic were not introduced.
- **Validation evidence:** `uv run python -m unittest discover -s tests -p 'test_*.py' -v` ran 20 tests with `OK`; `uv run python -m compileall -q src functions tests` passed; P03 review assertions passed; `git diff --check` passed.
- **Review-gate evidence:** Default local/test settings select local adapters; Catalyst, Neo4j, and LLM adapters raise typed disabled/unconfigured errors without network calls. Injected fake transports/backends verify typed request shapes and locked LLM fallback order. Neo4j boundary preserves Bolt `7687` and HTTP `7474`; connection settings remain centralized in `Settings`; only REST/SSE/multipart remain declared external protocols; no agent or engine access path was added.
- **Known blockers:** Actual Catalyst SDK, Neo4j driver, and LiteLLM provider compatibility remain intentionally unvalidated and deferred to later integration/deep-path phases. No credentials were required.

### Review record: P04 — Logical data contracts and synthetic fixtures

- **Status:** `COMPLETE`
- **Started:** 2026-07-25T18:34:27Z
- **Completed:** 2026-07-25T18:40:46Z
- **Implementation evidence:** Added locked enums and validated dataclasses in `src/domain/enums.py` and `src/domain/models.py`; deterministic ontology canonicalization and endpoint metadata in `src/domain/ontology.py`; explicit logical-to-Catalyst compatibility metadata in `src/domain/schema_mapping.py`; synthetic Karnataka context/generators in `data/generator/`; seed JSON fixtures in `data/seed/`; and `docs/data-contracts.md`.
- **Validation evidence:** `uv run python -m unittest discover -s tests -p 'test_*.py' -v` ran 29 tests with `OK`; `uv run python -m compileall -q src functions data tests` passed; schema-model assertions passed for all 11 logical tables; reproducible fixture counts were 12 FIRs, 48 FIR-entity links, 60 evidence-backed relationships, and 68 entities; fixture SHA-256 was `b72302398f351744c70af57cd1f06ffa0cb26a99175f4264ab88a0cff4b42cf2`; `git diff --check` passed.
- **Review-gate evidence:** Entity vocabulary contains exactly the 15 database-schema entity types; relationship vocabulary contains exactly 20 locked relationship types; card vocabulary contains the 5 logical card types; confidence/strength/vector/evidence/verification/card-subject constraints are tested; CCTNS FIR and station formats are tested; optional `IMEI`, `Evidence`, and `District` extensions are rejected until schema review; all model field sets map to known logical table fields; Catalyst deployment remains explicitly unvalidated; all generated narratives are marked synthetic and no real data is used.
- **Known blockers:** PostgreSQL extensions, triggers, partial indexes, expression keys, Catalyst schema syntax, and persistence remain intentionally unvalidated/deferred. P05 graph projection has not started.

### Review record: P05 — Neo4j projection and graph schema

- **Status:** `COMPLETE`
- **Started:** 2026-07-25T18:41:24Z
- **Completed:** 2026-07-25T18:46:57Z
- **Implementation evidence:** Added deterministic ID-keyed projection and bounded graph queries in `src/engines/graph_intelligence.py`; graph compatibility mapping from logical `DigitalEvidence` to the graph-boundary `Evidence` label; relationship evidence FIR IDs, discovery metadata, strength, verification, and verifier/timestamp properties; fixed-query health probe; pinned Neo4j `5.26.0-community` AppSail assets; loopback-only HTTP/Browser binding; Bolt configuration; memory settings; idempotent constraints/indexes; locked relationship vocabulary; health, schema initialization, and local backup/export scripts; and graph integration tests.
- **Validation evidence:** `uv run python -m unittest discover -s tests -p 'test_*.py' -v` ran **37 tests with `OK`**; `uv run python -m compileall -q src functions data tests` passed; targeted graph validation ran 8 tests with `OK`; `p05_asset_contract: passed`; final `p05_phase_boundary_contracts: passed`; `git diff --check` passed; `.LOCK/TODO.md` and `session-ses_0754.md` each passed individual `git check-ignore` assertions.
- **Review-gate evidence:** Projection replay is idempotent; traversal depth is bounded to `0..5`; relationship filters accept only the locked 20 relationship types; shortest paths return relationship citations; disabled-by-default Neo4j health returns unavailable without an injected driver; schema assets contain the locked labels/vocabulary and idempotent `IF NOT EXISTS` DDL; Bolt remains `7687`; HTTP remains loopback-only on `7474`; `7474` is not exposed by Docker; credentials are consumed only by operator scripts; and no arbitrary Cypher or public Browser route was added.
- **Deployment evidence:** Docker container smoke execution could not run because Docker Desktop integration is unavailable in the WSL 2 distro (`The command 'docker' could not be found in this WSL 2 distro`). Static Dockerfile/config/schema assertions and all projection tests passed as the required alternative validation path.
- **Known blockers:** Actual Neo4j driver wiring, Catalyst persistence, and live container schema execution remain intentionally deferred to the later integration/runtime phases; no deployment or performance claim is made.

### Review record: P06 — Typed T01–T23 registry

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T12:19:07Z
- **Completed:** 2026-07-26T12:21:26Z
- **Implementation evidence:** Added pinned `pydantic==2.11.7`; implemented all 23 Pydantic input contracts and typed output envelopes in `src/registry/schemas.py`; created the exact T01–T23 manifest with owners, deterministic/reasoning stages, authorization permissions, audit actions, citation requirements, public-route prohibition, and timeout budgets in `src/registry/manifest.py`; added fail-closed injected-handler dispatch and authorization context in `src/registry/tools.py` and `src/registry/dispatch.py`; exported the registry from `src/registry/__init__.py`; and added registry unit tests.
- **Validation evidence:** `uv lock` resolved the pinned dependency; `uv run python -m unittest discover -s tests -p 'test_*.py' -v` ran **46 tests with `OK`**; `uv run python -m compileall -q src functions data tests` passed; `p06_registry_completeness: passed`; `p06_phase_boundary_contracts: passed`; `git diff --check` passed; private-file ignore checks passed.
- **Review-gate evidence:** Exactly T01–T23 are registered; extra fields and invalid enum/range values are rejected; cross-field required subjects are validated; T15 is deterministic `lead_ranking`; T20 is `evidence_explainability`; T22 is `investigation_state` with `ADD_EVIDENCE`; unknown tools, unauthorized calls, public direct routes, over-budget calls, missing handlers, and invalid handler outputs fail closed; planner/tool parameters contain no unrestricted SQL/Cypher execution path; output contracts preserve citations and warnings.
- **Known blockers:** Registry handlers are injected boundaries only; deterministic retrieval/analysis engines and orchestration are intentionally deferred to P07–P13. No public API route or external service integration was added.

### Review record: P07 — Deterministic SQL and hybrid search engines

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T12:26:46Z
- **Completed:** 2026-07-26T12:28:37Z
- **Implementation evidence:** Added allowlisted structured FIR retrieval in `src/engines/sql_retrieval.py`; deterministic 1024-dimensional local embedding boundary in `src/shared/embedding.py`; shared retrieval contracts under `src/engines/retrieval/`; local vector index and explicit external-vector degradation in `src/engines/retrieval/vector.py`; BM25-compatible lexical scoring, RRF fusion with `k=60`, deterministic reranking, candidate limits, metadata filters, and citations in `src/engines/search_ranking.py`; and retrieval unit tests.
- **Validation evidence:** `uv run python -m unittest discover -s tests -p 'test_*.py' -v` ran **53 tests with `OK`**; `uv run python -m compileall -q src functions data tests` passed; targeted P07 tests ran 7 tests with `OK`; `p07_phase_boundary_contracts: passed`; `git diff --check` passed; private-file ignore checks passed.
- **Review-gate evidence:** Structured filters support exact FIR fields, status/priority/category/district/year, timezone-aware date ranges, ordering, field projection, counts, bounded limits, and FIR citations without an LLM; lexical/vector/hybrid results preserve source IDs, ranks, scores, and citations; RRF is fixed at `60`; candidate and vector limits are bounded at `100`; external vector failure explicitly returns local deterministic results with `VECTOR_BACKEND_UNAVAILABLE`; no raw SQL parser, unrestricted query, or provider call was added.
- **Known blockers:** Catalyst/ZCQL and pgvector capability compatibility remain unvalidated; the local deterministic embedding is an offline fallback and not a measured replacement for the configured BGE-M3 model. Evidence gate and fast-path release validation are intentionally deferred to P08.

### Review record: P08 — Fast-path execution and evidence gate

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T12:30:48Z
- **Completed:** 2026-07-26T12:32:21Z
- **Implementation evidence:** Added structured evidence contracts in `src/domain/evidence.py`; mandatory citation, numeric-consistency, permission, contradiction, uncertainty, and audit validation in `src/engines/evidence.py`; deterministic fast/deep classification in `src/orchestration/router.py`; synchronous cited execution in `src/orchestration/fast_path.py`; and unit tests for routing, release blocking, contradiction handling, and audit metadata.
- **Validation evidence:** `uv run python -m unittest discover -s tests -p 'test_*.py' -v` ran **61 tests with `OK`**; `uv run python -m compileall -q src functions data tests` passed; targeted P08 tests ran 8 tests with `OK`; `p08_phase_boundary_contracts: passed`; `git diff --check` passed; private-file ignore checks passed.
- **Review-gate evidence:** Fast path allows only T01/T02/T03/T06/T13/T14 deterministic tools; natural-language intent and reasoning tools route away from fast execution; released records require citations and source claims; inconsistent totals are blocked; contradictions are surfaced and block release; authorization remains enforced by the registry; audit metadata and deterministic uncertainty are attached; no LLM, private chain-of-thought, public tool route, or unrestricted query path was added.
- **Known blockers:** Fast path is currently an internal Python service boundary; REST/SSE exposure is intentionally deferred to P10. The evidence gate validates structured tool outputs and does not claim legal sufficiency.

### Review record: P09 — Persistent investigation state and checkpointing

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T13:44:00Z
- **Completed:** 2026-07-26T13:49:00Z
- **Implementation evidence:** Added `src/domain/investigation_state.py` with the Created/Active/Suspended/Closed/Archived lifecycle, versioned state aggregate, evidence board, notes, hypotheses, timeline, leads, graph view, deterministic health, provenance, and hash-chained audit metadata. Added `src/services/checkpoints.py` with atomic local JSON persistence and a Catalyst Data Store-compatible adapter; added `src/services/investigations.py`, `evidence_board.py`, `hypotheses.py`, `leads.py`, and `investigation_health.py` for authorized synchronized mutations.
- **Validation evidence:** Focused P09 suite ran **8 tests with `OK`**; full repository suite ran **69 tests with `OK`**; `uv run python -m compileall -q src functions data tests` passed; serialized state round-trip and checkpoint version assertions passed in `tests/unit/services/test_investigations.py`; `git diff --check` passed; private-file ignore checks passed.
- **Review-gate evidence:** Local checkpoints persist across fresh service instances; Catalyst-shaped storage uses the same state contract; lifecycle transitions fail closed; archived investigations are read-only; evidence/hypothesis/timeline/lead/graph mutations recalculate one shared state and health; health exposes deterministic coverage percentages, contradiction count, missing critical evidence, and metric-level source/calculation provenance; every mutation requires investigation authorization and appends auditable request/officer/version/hash metadata; stale checkpoint writes fail closed. No runner, workflow engine, agent runtime, or conversation-only memory was added.
- **Known blockers:** Catalyst deployment API compatibility and REST/SSE exposure remain deferred to P10; health thresholds are deterministic application policy and require later product review against measured investigation data.

### Review record: P10 — Capability/resource REST and SSE APIs

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T14:00:00Z
- **Completed:** 2026-07-26T14:05:00Z
- **Implementation evidence:** Added framework-neutral typed API contracts in `src/api/types.py`, cookie/bearer authentication in `src/api/auth.py`, SSE event serialization in `src/api/sse.py`, multipart validation in `src/api/multipart.py`, and the versioned `ApiApplication`/`RunnerProtocol` boundary in `src/api/application.py`. Added thin Catalyst delegates under `functions/api/` and documented the contract in `docs/api-reference.md`.
- **Validation evidence:** Focused P10 API suite ran **6 tests with `OK`**; full repository suite ran **75 tests with `OK`**; `uv run python -m compileall -q src functions data tests` passed; `git diff --check` passed; private-file ignore checks passed.
- **Review-gate evidence:** `/api/v1` resource and capability routes are versioned; P08 typed fast-path queries return synchronously; complex runs return REST run IDs and SSE streams; SSE events cover plan/evidence/error/done and use cookie-compatible auth; bearer auth is supported for fetch-based SSE clients; public T01–T23 routes are rejected; multipart framing, filename, type, and size limits are enforced; standardized errors include request IDs and CORS headers; API code imports only the Runner protocol and never LocalRunner or HexelRunner.
- **Known blockers:** FastAPI/AppSail mounting, Catalyst API Gateway/Auth deployment, live CORS validation, and production SSE transport remain deployment validation items. No live service, capacity, latency, or performance claim is made.

### Review record: P11 — Next.js investigation workspace with Feature-Sliced Design

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T14:10:00Z
- **Completed:** 2026-07-26T14:20:00Z
- **Implementation evidence:** Added the pinned `client/package.json` with Next.js 15.5.22, React 19.1.0, TypeScript 5.8.3, Tailwind CSS v4, Radix/shadcn-compatible primitives, Lucide, Motion, TanStack Query/Table, Zustand, React Hook Form/Zod, Cytoscape, ECharts, MapLibre, resizable panels, cmdk, Sonner, React DnD, react-markdown, React PDF, and next-themes. Added standalone AppSail-compatible `next.config.ts`, TypeScript/PostCSS/ESLint configuration, App Router layout/home/investigation routes, FSD `features`, `entities`, `widgets`, `shared`, and `styles` boundaries, typed REST and cookie-compatible SSE clients, and the investigation workspace shell.
- **Workspace evidence:** The shell renders one shared `InvestigationState` into Conversation, Evidence Board, Timeline, Network Graph, Leads, Hypothesis Panel, and Intelligence Cards; it displays Investigation Health, confidence/freshness fields, proactive intelligence before query entry, responsive layouts, and synthetic empty states only. The dynamic investigation route loads through the P10 REST client and falls back safely without changing backend contracts.
- **Validation evidence:** From `client/`, `npm run typecheck` passed; `npm run lint` passed with zero warnings after the ESLint 9 flat-config correction; `npm run build` passed on Next.js 15.5.22, compiling successfully and generating `/`, `/_not-found`, and `/investigations/[investigationId]`. The initial Next.js 15.5.7 installer warning was resolved by pinning the patched 15.5.22 release. Backend regression remains green at **75 tests with `OK`**, and Python compileall remains passed.
- **Review-gate evidence:** The implementation is investigation-first rather than chat-first; proactive alerts precede the question composer; no direct database/provider imports or real records are bundled; shared API/state types are below widgets/features under the FSD tree; REST/SSE/auth remain the only backend communication boundary; standalone output preserves Catalyst AppSail hosting without altering Functions, Runner, engines, Data Store, or Neo4j contracts.
- **Known blockers:** No browser automation dependency is installed, so visual/browser behavior is validated by the production build and responsive CSS paths rather than a headless browser run. Live Catalyst Auth/JWT, API Gateway, SSE, and AppSail deployment remain environment validation items. Full interaction mutation coverage and card-specific visualizations remain planned follow-on work in later phases.

### Review record: P12 — Temporary Runner and Strands agent fleet

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T14:30:00Z
- **Completed:** 2026-07-26T14:38:00Z
- **Implementation evidence:** Added `src/orchestration/runner.py` with the minimal async `Runner` protocol; `src/orchestration/state.py` with the immutable dependency-injected `AgentContext`; `src/orchestration/local_runner.py` with sequential state passing; and `src/orchestration/hexel_runner.py` with a future adapter protocol and explicit unavailable-runtime error. Added `src/agents/contracts.py` and package exports for Planner, Evidence, Graph Intelligence, Pattern Intelligence, Financial Intelligence, Timeline, Reasoner, and Reporter agent interfaces. No Strands/Hexel SDK dependency was introduced while the runtime is unavailable.
- **Validation evidence:** Focused P12 suite ran **7 tests with `OK`**. Full repository discovery ran **82 tests with `OK`**; `uv run python -m compileall -q src functions data tests` passed; `git diff --check` passed; an import audit found no direct database/provider imports in `src/orchestration` or `src/agents`.
- **Review-gate evidence:** `LocalRunner` only validates input, constructs `AgentContext`, invokes the declared agent sequence, passes each returned `InvestigationState` forward, and returns the final state. It has no persistence, scheduling, retries, streaming, distribution, cancellation, or workflow graph. Agents only accept context and return shared state; they do not invoke other agents or access Catalyst, Neo4j, or provider clients. `HexelRunner` satisfies the same structural protocol, delegates only to an injected future adapter, and never silently falls back to LocalRunner. Existing P08 fast-path tests remain green and the T01–T23 registry is unchanged.
- **Known blockers:** Agent business capabilities, deterministic intelligence engines, and real Strands model calls are intentionally deferred to P13 and later; Hexel runtime integration remains future deployment work. No local orchestration platform, gateway, skill system, policy engine, MCP server, or durable execution layer was added.

### Review record: P13 — Deterministic intelligence engines and agent business capabilities

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T14:45:00Z
- **Completed:** 2026-07-26T14:55:00Z
- **Implementation evidence:** Added shared typed provenance/uncertainty metadata in `src/engines/intelligence_types.py`; bounded graph centrality/community/path analysis in `src/engines/graph_analysis.py` exposed through the existing `graph_intelligence` boundary; deterministic MO/temporal patterns, behavioral profiles, financial flow/layering indicators, hotspot forecast signals, timeline reconstruction/gap detection, and evidence-weighted lead ranking in `src/engines/pattern_analysis.py`, `behavioral_profiling.py`, `financial_analysis.py`, `forecasting.py`, `timeline.py`, and `lead_ranking.py`. Added `src/agents/intelligence.py` capability agents that interpret validated engine results without recomputing facts.
- **Validation evidence:** Focused P13 suite ran **6 tests with `OK`**; full repository discovery ran **88 tests with `OK`**; `uv run python -m compileall -q src functions data tests` passed; deterministic repeated-input equality, source evidence extraction, bounds, empty/partial input behavior, and capability-agent validation were exercised.
- **Review-gate evidence:** Engine metadata records algorithm/version/parameters/input bounds; every non-empty signal carries source evidence; uncertainty is explicit and forecast outputs include intervals and limitations. Graph hops/candidates, event/transaction/observation counts, timeline size, and lead candidates are bounded. Agents accept typed validated results, preserve the shared `InvestigationState`, and mark findings for human review. No engine or agent declares guilt, legal sufficiency, or guaranteed future conduct; no LLM computes totals, paths, dates, scores, or forecasts; no orchestration/platform service was added.
- **Known blockers:** These are local deterministic business-capability implementations over supplied records; Catalyst/Neo4j production data wiring, measured forecast calibration, Strands model invocation, and scenario-scale performance validation remain later deployment/quality work. P14 owns intelligence-card materialization and lifecycle.

### Review record: P14 — Intelligence card materialization and lifecycle

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T15:05:00Z
- **Completed:** 2026-07-26T15:15:00Z
- **Implementation evidence:** Added `src/domain/cards.py` with all 15 locked product-card payload types, discriminated validation, confidence/provenance/timestamp/human-review requirements, freshness/status/version fields, and immutable lifecycle helpers. Added `src/services/cards.py` for canonical materialization, monotonically increasing versions, stale/archive transitions, and historical retrieval. Added `src/adapters/card_store.py` with an in-memory hot-cache implementation and atomic local canonical JSON plus metadata-index persistence.
- **Validation evidence:** Focused P14 card suite ran **4 tests with `OK`**; full repository discovery ran **92 tests with `OK`**; all 15 card types were instantiated and validated; canonical JSON survived a fresh local-store instance; version/supersession history, stale evaluation, archive, confidence bounds, and provenance requirements were exercised; compileall and `git diff --check` passed.
- **Review-gate evidence:** The card vocabulary is exactly the 15 locked product types and remains separate from logical entities. Storage follows canonical JSON → metadata index → hot cache; local storage uses atomic replacement and the adapter is intentionally provider-neutral. Card payloads carry engine/source provenance, confidence, timestamps, lifecycle status, and human-review markers; old versions remain retrievable. No card declares legal sufficiency, guilt, or guaranteed future conduct.
- **Known blockers:** Stratus/Catalyst Cache production API wiring, card event delivery, full React card-specific renderers, and measured retention/latency remain deployment or later integration work. P15 owns signals, proactive alerts, and entity resolution.

### Review record: P15 — Signals, proactive alerts, and entity resolution

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T15:25:00Z
- **Completed:** 2026-07-26T15:33:00Z
- **Implementation evidence:** Added `src/services/signals.py` and thin `functions/signals/` delegates for replay-safe synthetic FIR ingestion, source/entity validation, and active-investigation matching. Added `src/services/entity_resolution.py` with normalization, exact locked-identifier auto-merge boundaries, and explicit officer approval/rejection for Person suggestions. Added `src/services/proactive_alerts.py` to materialize authorized P14 alert cards, acknowledge/expire them, and enforce investigation scope.
- **Validation evidence:** Focused P15 suite ran **3 tests with `OK`**; full repository discovery ran **95 tests with `OK`**; replay/idempotency, active-investigation matching, Person approval, locked-identifier auto-merge, alert authorization, acknowledgement, and expiry were exercised; compileall and `git diff --check` passed.
- **Review-gate evidence:** Replaying an event does not invoke callbacks or duplicate signal state; only explicitly watched active investigations match; Person records never auto-merge; exact locked identifier types are the only auto-merge path; alert creation and mutation require investigation-scoped authorization; alerts are materialized as P14 cards with source provenance and a 48-hour policy TTL. No broad broadcast, silent merge, ungrounded alert, or direct provider/database integration was added.
- **Known blockers:** Catalyst Signals/Cron/Event Bus transport, production SSE alert delivery, measured delivery lag, richer matching rules, and card invalidation across external caches remain deployment/integration work. P16 owns RBAC, masking, immutable audit, and governance hardening.

### Review record: P16 — RBAC, masking, immutable audit, and governance hardening

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T14:45:00Z
- **Completed:** 2026-07-26T14:55:00Z
- **Implementation evidence:** Added `src/shared/auth.py` for external-claims-to-application-context adaptation, `src/shared/permissions.py` for the SHO/IO/DCP/Analyst/SP operation matrix and station/district/investigation scope checks, `src/shared/masking.py` for recursive Analyst PII masking and secret redaction, and `src/services/audit.py` for immutable SHA-512 chained audit records and verification. Added the thin `functions/signals/audit_logger.py` hook.
- **Validation evidence:** Focused P16 governance suite ran **3 tests with `OK`**; full repository discovery ran **98 tests with `OK`**; role/scope fail-closed checks, Analyst masking, secret-safe audit details, hash-chain verification, tamper detection, and human-review defaults were exercised; `uv run python -m compileall -q src functions data tests` and `git diff --check` passed.
- **Review-gate evidence:** Application checks cover reads, mutations, tools, agents, cards, alerts, exports, and reports through one operation matrix; investigation/station/district scope mismatches fail closed; Analyst output masks PII while preserving non-sensitive structure; audit details redact secrets before storage; each record chains to the previous SHA-512 digest and tampering invalidates verification; consequential records default to human review. Catalyst/Hexel policy is adapted at the boundary and not rebuilt locally.
- **Known blockers:** Live Catalyst Auth/Hexel policy integration, production audit persistence, external secret scanners, secure export transport, and deployment security validation remain environment work. P17 owns multilingual, voice, OCR, and report boundaries.

### Review record: P17 — Multilingual, voice, document, and report boundaries

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T15:45:00Z
- **Completed:** 2026-07-26T15:55:00Z
- **Implementation evidence:** Added optional local CPU model boundary `src/adapters/onnx/base.py` and exports for IndicTrans2, Faster-Whisper, Piper/Edge-TTS, and Tesseract model names. Added `src/services/voice.py` for Kannada/English translation with proper-noun preservation and voice transcription/synthesis degradation; `src/services/ocr.py` for optional OCR; and `src/services/reports.py` for authorized, classified, citation-qualified report documents. Existing `functions/api/upload_api.py` and P10 `MultipartParser` remain the upload boundary.
- **Validation evidence:** Focused P17/media/report/upload suite ran **10 tests with `OK`**; full repository discovery ran **102 tests with `OK`**; missing-model fallback, injected local asset loading, proper-noun preservation, report citations/classification/human-review language, cross-scope rejection, and existing multipart security tests passed; compileall and `git diff --check` passed.
- **Review-gate evidence:** No model asset is downloaded or network-loaded implicitly; absent assets return explicit degraded results; translation supports only English/Kannada and preserves supplied proper nouns; reports require non-empty source IDs/locators, authorized investigation scope, allowed classification, human-review language, and no legal/custody/guilt claims. P10 upload type/framing/size validation remains unchanged.
- **Known blockers:** Model smoke tests require local assets; live IndicTrans2/Whisper/Piper/Tesseract CPU/memory measurements, Catalyst Stratus report storage, and production upload/auth deployment remain environment validation items. P18 owns scenario wiring.

### Review record: P18 — Ten scenario integration suite and demo wiring

- **Status:** `COMPLETE`
- **Started:** 2026-07-26T16:05:00Z
- **Completed:** 2026-07-26T16:15:00Z
- **Implementation evidence:** Added `data/scenarios/` with ten deterministic synthetic fixtures matching the locked scenarios: vehicle theft, cybercrime repeat offender, UPI money trail, hotspot forecast, linked robbery hypothesis, proactive FIR match, entity resolution, drug network, investigation handover, and strategic briefing. Added `tests/integration/scenarios/test_scenarios.py`, `scripts/seed_demo.py`, `scripts/smoke_demo.py`, and `docs/demo-script.md`. The primary demo order is encoded as `3 → 1 → 6 → 5 → 4 → 10`.
- **Validation evidence:** Focused P18 scenario suite ran **3 tests with `OK`**; full repository discovery ran **105 tests with `OK`**; seed and smoke scripts ran locally without external services; all ten scenarios have routes, engines, cards, synthetic citations, deterministic fallbacks, and replay-stable digests; Scenario 6 is system-initiated with no opening query; compileall and `git diff --check` passed.
- **Review-gate evidence:** Fixtures contain no real records and enforce `SYNTHETIC-*` citations. Scenario assertions cover fast/deep/signals routes, relevant engine/card metadata, proactive-first behavior, deterministic replay, demo ordering, and provider-independent local fallback. The demo documentation explicitly avoids claims of measured accuracy, capacity, latency, or real investigative outcomes.
- **Known blockers:** P19 owns performance, quality, capacity, and resilience measurement; no scenario fixture is evidence of production accuracy or throughput. P20 owns final architecture/security/demo review.

### Architecture migration record — temporary runtime strategy (pre-P09)

- **Status:** `COMPLETE`
- **Date:** 2026-07-26
- **Decision:** Hexel Studio owns the production agent platform. Until it is available, KSP implements only a minimal `Runner`/`LocalRunner` that invokes Strands agents, passes `InvestigationState`, and returns the final state. KSP will not recreate orchestration, gateways, skills, policies, MCP, memory, observability, or platform governance.
- **Implementation evidence:** Replaced the prior platform-like runtime addendum with the temporary Runner architecture in `docs/orchestration-architecture.md`; made `InvestigationService → Runner (Protocol) → LocalRunner/HexelRunner` explicit; standardized the minimal AgentContext contract; documented P08 fast-path bypass; updated README wording and P10/P12/P13/P16/constraint/review sections in this phase plan. P12 now covers only the Runner and Strands agents; P13 covers deterministic engines and agent business capabilities.
- **Source-of-truth migration evidence:** By explicit user authorization recorded in `transcript.md`, the non-private runtime sections of `.LOCK/architecture.md`, `.LOCK/ai-architecture.md`, `.LOCK/AGENTS.md`, `.LOCK/DECISIONS.md`, `.LOCK/investigation-engine.md`, `.LOCK/vision.md`, and `.LOCK/prd.md` were reconciled with the final Runner/Strands strategy. `.LOCK/TODO.md` and `session-ses_0754.md` remain ignored and untouched.
- **Preserved contracts:** Domain models, database/schema mapping, ontology, T01–T23 registry, deterministic engines, Catalyst authority, Neo4j projection role, REST/SSE protocols, frontend requirements, and P08 fast path/evidence gate are unchanged.
- **Review evidence:** No external orchestration framework or new platform runtime dependency/import exists in Python source; no separate gateway/platform folders were added; existing registry and LLM adapters remain the integration boundaries; P08 is independent of any Runner; private-file checks and regression tests pass.
- **Known blockers:** Strands agent implementation and the minimal LocalRunner are planned for P12; real Hexel integration is future work. P09 remains the next implementation phase.

### Review records: P09–P20

- **Status:** `PLANNED`
- **Evidence:** not started
