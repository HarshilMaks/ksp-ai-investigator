# KSP INVESTIGATEAI — CRIME INTELLIGENCE OPERATING SYSTEM

> 🔒 LOCKED — All decisions final. Selected implementation baseline. Performance, capacity, cost, and quality figures are targets or estimates pending benchmark/validation.
> Date: 2026-07-24 | Constraint: $0 + Zoho Catalyst ($250 credits) + Open Source
> Product positioning: **Crime Intelligence Operating System** — not a chatbot, not a dashboard.
> Core principle: **AI interprets intent and explains evidence. Deterministic engines compute facts. Humans review consequential conclusions.**

---

## 0. PRODUCT-LEVEL ARCHITECTURE (NEW)

### The product is investigations, not conversations

```text
Other teams: Question → Answer → Done
This product: Investigation → Question → Evidence → Updated Investigation → Next Question → ...
```

### Key product decisions

| Decision | Choice |
|----------|--------|
| Product unit | Persistent Investigation (with lifecycle: active/suspended/closed/archived) |
| Workspace | 7-panel: Conversation, Evidence Board, Timeline, Network Graph, Leads, Hypotheses, Intelligence Cards |
| Output type | Structured artifacts (cards, timelines, graphs, leads, reports) over text responses |
| Intelligence model | Proactive: system discovers and alerts without being asked |
| Hypothesis system | Structured for/against/missing evidence evaluation with officer control |
| Entity resolution | Fuzzy/exact/phonetic/contextual matching with officer-approved merges |
| Case memory | Full session persistence: evidence, hypotheses, annotations, leads, graph state |
| Intelligence cards | 15 precomputed card types that become the UI layer |
| Demo scenarios | 10 end-to-end investigations that serve as integration tests and demo script |

### New documents added

- `investigation-workspace.md` — the product heart
- `intelligence-cards.md` — 15 card types (the precomputed intelligence layer)
- `investigation-scenarios.md` — 10 investigation stories with full traces and demo script

---

## 1. CATALYST FREE TIER BUDGET (Monthly)

| Service | Free Limit | Strategy |
|---------|-----------|----------|
| Functions | 25,000 GB-sec | All agents, APIs, tools |
| AppSail | 15 GB-hrs | Neo4j (512MB). Use credits for always-on |
| Data Store | 2GB, 10K SELECTs, 5K INSERTs | Pre-compute, batch, cache. Credits for overages |
| Cache | 1K GETs, 5K PUTs | Hot intelligence cards + session state |
| API Gateway | 100K requests | Sufficient |
| Zia | 100 calls/month | Demo-only. Dev uses open source |
| QuickML | 500 predictions | Demo-only |
| SmartBrowz | 5 hrs headless | PDF reports |
| Stratus | $0.02/GB (credits) | Intelligence JSONs, data, reports |
| Circuits/Signals/Cron | Included | Workflows, events, scheduling |

**Total Budget**: $250 trial credits (180 days) are planned to cover expected development/demo overages; actual usage must be monitored.

---

## 2. GRAPH DATABASE: Neo4j 5.x Community on AppSail Docker

- GDS: Louvain, PageRank, Betweenness, Shortest Path, Node Similarity
- APOC: Path expansion, text processing, periodic execution
- Container: 512MB RAM; initial target is 200K nodes + 500K edges, subject to AppSail load testing
- Persistence: Docker volume (survives restarts)
- Backup: Nightly Cypher export → Stratus

---

## 3. LLM: Multi-Provider Free (Groq Primary + Gemini Secondary)

| Provider | Model | Role | Limits |
|----------|-------|------|--------|
| Groq | Llama 3.3 70B | Planning, chat, tool selection | 30 RPM, 14.4K RPD |
| Gemini 2.5 Flash | gemini-2.5-flash | Deep reasoning, hypothesis, reports | 10 RPM, 250 RPD |
| Mistral | mistral-small | Bulk extraction, summarization | 1B tokens/month |
| OpenRouter | llama-3.1-8b:free | Emergency fallback | 50-1000 RPD |

All use OpenAI SDK format. LiteLLM router for auto-failover.

---

## 4. EMBEDDINGS: BGE-M3 ONNX INT8 (CPU, In-Process)

- Model: `AlpEge/bge-m3-onnx-int8` (HuggingFace)
- Dimensions: 1024 dense + sparse + ColBERT
- Runtime: ONNX Runtime CPU in Catalyst Function
- Latency: estimated ~60-100ms per document; validate on the deployed Catalyst runtime
- Languages: 100+ including EN + KN code-mixed
- Strategy: Pre-compute ALL 50K FIRs offline. Only embed queries at runtime.
- Cost: $0

---

## 5. RERANKER: BGE-Reranker-v2-m3 ONNX (CPU, In-Process)

- Model: `Sophia-AI/bge-reranker-v2-m3-onnx`
- Runtime: ONNX Runtime CPU
- Latency: estimated ~50ms for 20 pairs; validate on the deployed Catalyst runtime
- Pipeline: RRF top-60 → Rerank → Return top-5
- Cost: $0

---

## 6. VECTOR SEARCH: pgvector HNSW in Catalyst Data Store

- Index: HNSW (cosine similarity)
- Capacity target: 50K FIR + 200K entity vectors; validate storage, index build, and query behavior on Catalyst Data Store
- Latency target: estimated 5-20ms for top-100 ANN; validate on the deployed Data Store
- Hybrid: SQL filters + vector in single query
- Cost: $0 (included in Data Store)

---

## 7. STT (Speech-to-Text): Faster-Whisper on CPU

- Engine: Faster-Whisper (CTranslate2) — base model
- Languages: English + Kannada (multilingual model)
- Latency target: approximately 2x realtime on CPU; validate with representative English/Kannada audio
- Demo Strategy: Pre-recorded audio for live demo reliability
- Fallback: Groq Whisper API (free, ultra-fast) for short clips
- Catalyst Zia: 100 calls/month — reserve for demo only
- Cost: $0

---

## 8. TTS (Text-to-Speech): Piper ONNX + Edge TTS

- Primary: Piper TTS (ONNX, Kannada voice model) — runs in Function
- Fallback: Edge TTS (Microsoft, free neural voices for Kannada)
- Latency: Real-time (Piper) / ~200ms (Edge TTS)
- Demo Strategy: Pre-generate common TTS responses; live for novel queries
- Cost: $0

---

## 9. TRANSLATION: IndicTrans2 (AI4Bharat) ONNX

- Model: IndicTrans2 200M distilled (ONNX export)
- Quality target: evaluate Kannada-English quality against a labeled sample; the cited BLEU result is external evidence, not a project guarantee
- Runtime: ONNX CPU in Function
- Latency target: approximately 200ms per sentence; validate on the deployed Catalyst runtime
- Code-mixing: BGE-M3 handles code-mixed queries natively
- Cost: $0

---

## 10. OCR / DOCUMENT PROCESSING: Tesseract + Layout Parser

- OCR: Tesseract 5.x (Kannada + English trained data)
- Layout: LayoutParser (document structure detection)
- Use case: Scanned FIRs, handwritten notes (stretch goal)
- Runtime: In Function (CPU)
- Catalyst Zia OCR: 100 calls — demo only
- Cost: $0

---

## 11. FRONTEND: React 18 + Vite on Catalyst Slate

- Framework: React 18 + TypeScript + Vite
- Hosting: Catalyst Slate (Web Client Hosting)
- State: Zustand (client) + LangGraph Checkpointer (server persistence)
- Real-time: SSE for AI/progress/alert streams; WebSocket is deferred until multi-investigator collaboration is required
- Visualization: Cytoscape.js (graphs), ECharts (Sankey/heatmaps/timelines), MapLibre GL (maps), Deck.gl H3 (hexagons)
- Cost: $0

---

## 12. ORCHESTRATION: LangGraph Orchestrator + Reasoning Agents + Deterministic Engines

- **Investigation Orchestrator**: LangGraph state machine, not an LLM agent. Manages routing, state, parallel execution, retries, checkpoints, and SSE progress.
- **Planner Agent**: LLM-powered and invoked only for ambiguous or complex queries. Converts natural language into a validated execution plan; it never emits unrestricted SQL or Cypher.
- **Reasoning Agent**: LLM-powered grounded synthesis over structured engine outputs, supporting/contradicting evidence, missing evidence, and hypotheses.
- **Reporter Agent**: LLM-powered communication layer for investigator summaries, timelines, lead explanations, bilingual responses, and report wording.
- **Decision Support**: **Deterministic Lead Ranking Engine** with optional LLM explanation; it is not an autonomous decision-maker.
- **Deterministic engines**: SQL Retrieval, Search/Ranking, Graph Intelligence, Pattern Analysis, Behavioral Profiling, Financial Analysis, Forecasting, Timeline, and Evidence/Explainability.
- **Execution paths**:
  - Fast path: simple structured query → deterministic engine → evidence/citation response.
  - Deep path: Planner → parallel engines → evidence reconciliation → Reasoner → lead ranking → Reporter.
- **Background Workflows**: Catalyst Circuits for multi-step jobs, Catalyst Cron for scheduled intelligence, and Catalyst Signals for incremental ingestion/update events.
- **Model routing**: LiteLLM selects Groq, Gemini, Mistral, or OpenRouter by task, complexity, quota, and fallback state; agents never hardcode a provider.
- **Cost**: Minimize LLM calls; deterministic computation is preferred for every fact, count, score, path, and date.

### Governing principle

> **AI interprets intent and explains evidence. Deterministic engines compute facts. Humans review consequential conclusions.**

---

## 13. API & CONNECTION ARCHITECTURE — FINAL HYBRID DECISION

### External communication

- **Catalyst API Gateway** is the public entry point for authentication, RBAC, throttling, and routing.
- **Capability-oriented REST APIs** expose investigation actions rather than database tables:
  - `POST /api/v1/investigations/{id}/query`
  - `POST /api/v1/investigations/{id}/network-analysis`
  - `POST /api/v1/investigations/{id}/profile-offender`
  - `POST /api/v1/investigations/{id}/similar-cases`
  - `POST /api/v1/investigations/{id}/hypothesis`
  - `POST /api/v1/investigations/{id}/generate-report`
- **Resource REST APIs** remain available for workspace state: investigations, evidence, timeline, notes, and reports.
- **SSE** streams investigation plans, tool progress, evidence cards, reasoning, tokens, alerts, and completion events.
- **Multipart REST** handles voice/audio uploads and document uploads.
- Complex investigations use `POST` to create a run, followed by an SSE stream. Simple lookups may return synchronously.

### Internal AI communication

- The LangGraph Investigation Engine communicates with an **internal typed Python Tool Registry** through direct calls in the same runtime for low latency and strong schemas.
- Tools invoke the Data Store, pgvector, Neo4j Bolt, ONNX models, Stratus, and intelligence cards. Agents do not access databases directly.
- Catalyst Signals carry backend data-change events; Cron and Circuits run scheduled and multi-step workflows.
- **gRPC is reserved for a future split into independent internal services** and is not used in the initial Catalyst deployment.
- **MCP is an optional interoperability adapter** over the typed registry; it is not a runtime dependency and is not exposed directly to investigators.
- WebSockets are deferred until collaborative multi-investigator editing or presence is required.

```
Browser (React/Slate)
    │ REST capability/resource APIs + SSE + Multipart
    ▼
Catalyst API Gateway (Auth + RBAC + Rate Limit)
    │
    ▼
Capability API / BFF (Catalyst Functions or FastAPI on AppSail)
    ├─► LangGraph Investigation Engine
    │       ├─► Planner + typed internal Tool Registry
    │       ├─► Groq/Gemini/Mistral (OpenAI SDK, LiteLLM router)
    │       ├─► Catalyst Data Store (SQL + pgvector)
    │       ├─► Neo4j on AppSail (Bolt protocol, port 7687)
    │       ├─► BGE-M3 / reranker / IndicTrans2 ONNX models
    │       ├─► Faster-Whisper and Piper for voice
    │       └─► Stratus (pre-computed intelligence JSONs)
    │
    ├─► SSE event stream back to the workspace
    ├─► Catalyst Circuits (background workflows)
    ├─► Catalyst Signals (data-change event bus)
    ├─► Catalyst Cron (scheduled jobs)
    └─► Catalyst Cache (Redis — hot data)
```

---

## 13A. EXECUTION, ACCURACY, AND SCALE DECISIONS

### Fast/deep query routing

```text
Query
  ├─ Exact, structured, low-risk → Fast path
  │    SQL/Graph/Search engine → Evidence validator → Response
  │
  └─ Ambiguous, relational, or hypothesis query → Deep path
       Planner → parallel engines → evidence reconciliation
       → Reasoning Agent → lead ranking → Reporter
```

### Evidence gate

No response is released until the Evidence/Explainability Engine checks:

- Every factual claim has a source FIR, entity, relationship, or computed result.
- Returned numbers match deterministic engine outputs.
- Contradicting evidence is surfaced.
- Restricted data is filtered by user role and investigation scope.
- Low-confidence or incomplete results are explicitly qualified.
- The full tool plan, sources, calculations, and model metadata are audit-recorded.

### Resource optimization

- Do not call an LLM for exact filters, counts, joins, graph paths, totals, dates, or deterministic scores.
- Precompute network cards, profiles, hotspots, forecasts, financial summaries, and similar-case indexes.
- Batch embeddings and writes; use cursor pagination and idempotent ingestion.
- Rerank only a small fused candidate set; do not pass the full dataset to an LLM.
- Cache plans, prepared intelligence cards, and repeated safe queries.
- Apply provider quotas, token budgets, circuit breakers, and graceful fallback routing.
- Run independent engines in parallel and stream progress through SSE.

### Scale targets

The initial target is 50K FIRs, 200K entities/vectors, and 500K relationships, subject to deployment benchmarks. State-wide sizing is a future scale test, not a current guarantee. Acceptance metrics are measured p50/p95/p99 latency, Precision@K/Recall@K, entity-resolution accuracy, citation coverage, unsupported-claim rate, Kannada/English parity, and cost per investigation.

---

## 14. DECISION MATRIX (Final)

| Slot | Decision | Cost |
|------|----------|------|
| Platform | Zoho Catalyst (mandatory) | $250 credits |
| Graph DB | Neo4j 5.x Community (AppSail Docker) | Credits |
| LLM Primary | Groq Llama 3.3 70B | $0 |
| LLM Secondary | Google Gemini 2.5 Flash | $0 |
| LLM Tertiary | Mistral Small | $0 |
| Embeddings | BGE-M3 ONNX INT8 (CPU) | $0 |
| Reranker | BGE-Reranker-v2-m3 ONNX (CPU) | $0 |
| Vector DB | pgvector in Data Store | $0 |
| Graph Algos | Neo4j GDS (Louvain, PageRank, etc.) | $0 |
| STT | Faster-Whisper base (CPU) | $0 |
| TTS | Piper ONNX + Edge TTS | $0 |
| Translation | IndicTrans2 200M ONNX | $0 |
| OCR | Tesseract 5.x | $0 |
| Frontend | React 18 + Vite (Slate) | $0 |
| AI orchestration | LangGraph orchestrator + Planner/Reasoning/Reporter agents | $0 |
| Deterministic engines | SQL, Search/Ranking, Graph, Pattern, Profiling, Financial, Forecasting, Timeline, Evidence | $0 |
| Internal tools | Typed T01–T23 registry; engines are not LLM agents | $0 || Workflows | Catalyst Circuits | $0 |
| Events | Catalyst Signals | $0 |
| Scheduling | Catalyst Cron | $0 |
| **TOTAL** | | **$0 + $250 credits** |

---

## 15. FREE TIER BUDGET TRACKER (Monthly Estimate)

| Resource | Free Limit | Est. Usage (Dev) | Est. Usage (Demo) | Status |
|----------|-----------|-----------------|-------------------|--------|
| Functions | 25K GB-sec | ~15K GB-sec | ~5K GB-sec | ✅ Within |
| AppSail | 15 GB-hrs | ~45 GB-hrs (Neo4j 24/7) | ~15 GB-hrs | ⚠️ Use credits ($2.40/month) |
| Data Store SELECTs | 10K | ~50K | ~5K | ⚠️ Use credits (~$2.40) |
| Data Store INSERTs | 5K | ~60K (initial load) | ~500 | ⚠️ Use credits (~$5.50) |
| Cache | 6K ops | ~4K | ~2K | ✅ Within |
| API Gateway | 100K | ~30K | ~10K | ✅ Within |
| SmartBrowz | 5 hrs | ~2 hrs | ~1 hr | ✅ Within |
| **Total Monthly Overage** | | ~$10-15 | ~$5 | **Well within $250 credits** |

---

## 16. IMPLEMENTATION PRIORITY (8 Weeks)

| Week | Focus | Milestone |
|------|-------|-----------|
| 1 | Foundation | Catalyst project, schema, synthetic data (10K FIRs), Auth, Neo4j up |
| 2 | Retrieval | 4-way hybrid retriever working (SQL+Vector+Graph+BM25→RRF→Rerank) |
| 3 | Orchestration | LangGraph fast/deep router + Planner/Reasoner/Reporter + typed registry |
| 4 | Intelligence | Deterministic SQL, Graph, Pattern, Profiling, Financial, Forecast, Timeline, Search, Evidence engines |
| 5 | Workspace | React workspace: 6 panels, chat streaming, graph viz, timeline |
| 6 | Multilingual + Governance | IndicTrans2, voice demo, audit log, RBAC, explainability |
| 7 | Demo Scenarios | 5 scripted investigations wired end-to-end, polished |
| 8 | Polish + Submit | Video, presentation, benchmarks, stress test, submission |

---

## 17. KEY TECHNICAL RISKS & MITIGATIONS

| Risk | Probability | Mitigation |
|------|------------|------------|
| AppSail cold start (Neo4j) | High | Keep warm via cron ping every 4 min; use credits for dedicated |
| Groq rate limits during demo | Medium | Gemini auto-fallback via LiteLLM; pre-cache common demo queries |
| ONNX models too large for Function RAM | Medium | Use INT8 quantized models; lazy-load; warm-up on deploy |
| Data Store operation limits | High | Batch operations, aggressive caching, pre-compute intelligence |
| Kannada voice quality | Medium | Pre-record demo audio; Piper + Edge TTS dual pipeline |
| Neo4j memory at 512MB | Low | Initial 200K-node/500K-edge target requires load testing; use streaming GDS and tune memory based on measurements |
| Team velocity | Medium | Frozen scope after Week 2; parallel tracks (BE/FE/Data) |

---

## 18. ARCHITECTURE LOCK CONFIRMATION

These decisions are FINAL:

1. ✅ Catalyst-native (every mandated service used)
2. ✅ Neo4j on AppSail (GDS algorithms for criminal network analysis)
3. ✅ Groq + Gemini (multi-provider, zero cost, auto-failover)
4. ✅ BGE-M3 INT8 ONNX (CPU embeddings, multilingual, dense+sparse)
5. ✅ BGE-Reranker-v2-m3 ONNX (CPU cross-encoder reranking)
6. ✅ pgvector HNSW (co-located vector search)
7. ✅ Faster-Whisper + Piper (CPU voice, demo-ready)
8. ✅ IndicTrans2 ONNX (best Kannada translation)
9. ✅ LangGraph orchestrator + Planner/Reasoner/Reporter + 23-tool typed registry + deterministic engines
10. ✅ React 18 + Slate (6-panel investigation workspace)
11. ✅ Pre-computed intelligence (Cron + Signals; direct lookup target, measured during validation)
12. ✅ Tamper-evident audit log (hash-chained; legal admissibility requires separate review)
13. ✅ 5 Demo scenarios (scope frozen)
14. ✅ 8-week plan (no scope additions after Week 2)
