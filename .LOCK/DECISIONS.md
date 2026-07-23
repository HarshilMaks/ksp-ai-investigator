# KSP INVESTIGATEAI — MASTER ARCHITECTURE DECISIONS

> 🔒 LOCKED — All decisions final. No options. No debates. Best-in-class selected.
> Date: 2026-07-23 | Constraint: $0 + Zoho Catalyst ($250 credits) + Open Source

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

**Total Budget**: $250 trial credits (180 days) covers ALL overages.

---

## 2. GRAPH DATABASE: Neo4j 5.x Community on AppSail Docker

- GDS: Louvain, PageRank, Betweenness, Shortest Path, Node Similarity
- APOC: Path expansion, text processing, periodic execution
- Container: 512MB RAM, handles 200K nodes + 500K edges
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
- Latency: ~60-100ms per doc
- Languages: 100+ including EN + KN code-mixed
- Strategy: Pre-compute ALL 50K FIRs offline. Only embed queries at runtime.
- Cost: $0

---

## 5. RERANKER: BGE-Reranker-v2-m3 ONNX (CPU, In-Process)

- Model: `Sophia-AI/bge-reranker-v2-m3-onnx`
- Runtime: ONNX Runtime CPU
- Latency: ~50ms for 20 pairs
- Pipeline: RRF top-60 → Rerank → Return top-5
- Cost: $0

---

## 6. VECTOR SEARCH: pgvector HNSW in Catalyst Data Store

- Index: HNSW (cosine similarity)
- Capacity: 50K FIR + 200K entity vectors
- Latency: 5-20ms top-100 ANN
- Hybrid: SQL filters + vector in single query
- Cost: $0 (included in Data Store)

---

## 7. STT (Speech-to-Text): Faster-Whisper on CPU

- Engine: Faster-Whisper (CTranslate2) — base model
- Languages: English + Kannada (multilingual model)
- Latency: ~2x realtime on CPU
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
- Quality: BEST for Kannada-English (BLEU 21.2, beating NLLB)
- Runtime: ONNX CPU in Function
- Latency: ~200ms per sentence
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
- Real-time: SSE for LLM streaming + Catalyst Signals → WebSocket for alerts
- Visualization: Cytoscape.js (graphs), ECharts (Sankey/heatmaps/timelines), MapLibre GL (maps), Deck.gl H3 (hexagons)
- Cost: $0

---

## 12. ORCHESTRATION: LangGraph + Catalyst Circuits

- Agent Orchestration: LangGraph (Python) — stateful, checkpointed, parallel tool calls
- Background Workflows: Catalyst Circuits (daily intelligence refresh, multi-step investigations)
- Scheduling: Catalyst Cron (02:00-05:00 daily intelligence compute)
- Events: Catalyst Signals (new FIR → entity extraction → embedding → alert)
- Cost: $0

---

## 13. CONNECTION ARCHITECTURE

```
Browser (React/Slate)
    │ REST + SSE
    ▼
Catalyst API Gateway (Auth + RBAC + Rate Limit)
    │
    ▼
Catalyst Functions (Python 3.11)
    ├─► LangGraph Orchestrator
    │       ├─► Groq/Gemini/Mistral (OpenAI SDK, LiteLLM router)
    │       ├─► Catalyst Data Store (SQL + pgvector)
    │       ├─► Neo4j on AppSail (Bolt protocol, port 7687)
    │       ├─► BGE-M3 ONNX (in-process embedding)
    │       ├─► BGE-Reranker ONNX (in-process reranking)
    │       ├─► IndicTrans2 ONNX (in-process translation)
    │       ├─► Faster-Whisper (in-process STT)
    │       ├─► Piper ONNX (in-process TTS)
    │       └─► Stratus (pre-computed intelligence JSONs)
    │
    ├─► Catalyst Circuits (background workflows)
    ├─► Catalyst Signals (event bus)
    ├─► Catalyst Cron (scheduled jobs)
    └─► Catalyst Cache (Redis — hot data)
```

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
| Agents | LangGraph (Python) | $0 |
| Workflows | Catalyst Circuits | $0 |
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
| 3 | Agents | LangGraph orchestrator + Planner + Collector + Reasoner agents |
| 4 | Intelligence | Pre-computed engines: Network, Pattern, Profiler, Financial (Cron) |
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
| Neo4j memory at 512MB | Low | 200K nodes + 500K edges fits ~400MB; GDS streams, doesn't materialize |
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
9. ✅ LangGraph + 23-Tool Registry (agent fleet orchestration)
10. ✅ React 18 + Slate (6-panel investigation workspace)
11. ✅ Pre-computed intelligence (Cron + Signals, O(1) at query time)
12. ✅ Immutable audit log (hash-chained, court-admissible)
13. ✅ 5 Demo scenarios (scope frozen)
14. ✅ 8-week plan (no scope additions after Week 2)
