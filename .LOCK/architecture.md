# KSP InvestigateAI — Overall System Architecture
> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24


> Capstone Architecture Document  
> Version: 1.0.0  
> Last Updated: 2026-07-23  

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Deployment Topology](#2-deployment-topology)
3. [Data Flow](#3-data-flow)
4. [Performance Architecture](#4-performance-architecture)
5. [Security Architecture](#5-security-architecture)
6. [Scalability](#6-scalability)
7. [Monitoring & Observability](#7-monitoring--observability)
8. [Project Structure](#8-project-structure)
9. [Integration Points](#9-integration-points)

---

## 1. System Overview

### Layered Architecture (6 Layers)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                                      │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Catalyst AppSail — Next.js 15 App Router + React 19                        │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────────────┐    │    │
│  │  │ Chat Panel │ │ Graph View │ │ Intel Cards│ │ Investigation Ws  │    │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └───────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │ REST capability/resource APIs + SSE
┌──────────────────────────────────────▼──────────────────────────────────────────┐
│                              API LAYER                                            │
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ API Gateway  │  │ Catalyst Auth│  │ Rate Limiting│  │ Request Routing  │    │
│  │ (Managed)    │  │ (JWT+Session)│  │ (per-role)   │  │ (path-based)     │    │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  └──────────────────┘    │
└─────────┼───────────────────────────────────────────────────────────────────────┘
          │ Function invocation
┌─────────▼───────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                                       │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  LangGraph Investigation Orchestrator (State Machine; not an LLM agent)                     │    │
│  │                                                                          │    │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐    │    │
│  │  │ Router  │──▶│ Planner? │──▶│ Engines  │──▶│ Evidence Gate    │    │    │
│  │  │         │   │Reasoner │   │ T01–T23  │   │ + Reporter       │    │    │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────────────┘    │    │
│  │       │              │                                                   │    │
│  │       ▼              ▼                                                   │    │
│  │  ┌──────────────────────────────────────┐                               │    │
│  │  │  External LLMs (via LiteLLM)         │                               │    │
│  │  │  ┌───────┐  ┌────────┐  ┌─────────┐ │                               │    │
│  │  │  │ Groq  │  │ Gemini │  │ Mistral │ │                               │    │
│  │  │  │Llama 3.3│ │ 2.5 Flash│ │ Small   │ │                               │    │
│  │  │  │(fast) │  │(reason)│  │(fallbck)│ │                               │    │
│  │  │  └───────┘  └────────┘  └─────────┘ │                               │    │
│  │  └──────────────────────────────────────┘                               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                       │
│  │   Circuits    │  │    Signals    │  │     Cron      │                       │
│  │ (Workflows)   │  │ (Event-driven)│  │ (Scheduled)   │                       │
│  └───────────────┘  └───────────────┘  └───────────────┘                       │
└─────────┬───────────────────────────────────────────────────────────────────────┘
          │ Tool calls + queries
┌─────────▼───────────────────────────────────────────────────────────────────────┐
│                          RETRIEVAL LAYER                                          │
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Vector Search│  │Graph Traversal│  │  ZCQL Query  │  │  ONNX Inference │    │
│  │ (embeddings) │  │ (Cypher/GDS) │  │ (relational) │  │  (in-process)   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────────────────┘    │
└─────────┼──────────────────┼──────────────────┼─────────────────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────────────────────────┐
│                            DATA LAYER                                             │
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Data Store  │  │    Neo4j     │  │   Stratus    │  │  Catalyst Cache  │    │
│  │  (ZCQL/SQL)  │  │  (AppSail)  │  │ (File Store) │  │  (Key-Value)     │    │
│  │              │  │  GDS + APOC  │  │              │  │                  │    │
│  │ • FIRs       │  │ • Entities   │  │ • Pre-computed│  │ • Session state  │    │
│  │ • Users      │  │ • Relations  │  │   JSON cards │  │ • Query results  │    │
│  │ • Audit logs │  │ • Embeddings │  │ • ONNX models│  │ • Graph snapshots│    │
│  │ • Configs    │  │ • Communities│  │ • Reports    │  │ • LLM responses  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                                       │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Zoho Catalyst Platform (Managed)                                        │    │
│  │                                                                          │    │
│  │  • Auto-scaling compute    • TLS termination     • DNS management       │    │
│  │  • Container orchestration • Secret management   • CI/CD Pipelines      │    │
│  │  • Monitoring & logging    • Backup & recovery   • Free tier management │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐          │
│  │  External Services                                                 │          │
│  │  ┌───────────┐  ┌────────────┐  ┌───────────┐  ┌──────────────┐  │          │
│  │  │ Groq API  │  │ Google AI  │  │ Mistral AI│  │  SmartBrowz  │  │          │
│  │  │ (primary) │  │ (Gemini)   │  │ (fallback)│  │  (scraping)  │  │          │
│  │  └───────────┘  └────────────┘  └───────────┘  └──────────────┘  │          │
│  └───────────────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Service Connectivity Map

```
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │ HTTPS
                    ┌──────▼──────┐
                    │  API Gateway │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼───┐ ┌─────▼────┐ ┌────▼─────┐
       │ Auth     │ │ API Fns  │ │ AppSail  │
       │ (verify) │ │ (planned; capacity pending validation)    │ │ (static) │
       └──────────┘ └─────┬────┘ └──────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼───┐    ┌──────▼───┐    ┌───────▼──────┐
   │Data Store│    │  Neo4j   │    │   Stratus    │
   │ (ZCQL)  │    │(AppSail) │    │ (Files/JSON) │
   └──────────┘    └──────────┘    └──────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Cache     │
                    │ (L2 layer)  │
                    └─────────────┘
```

---

## Execution contract: fast path, deep path, and evidence gate

```text
Exact/structured query → deterministic engine → Evidence/Explainability gate → response

Ambiguous/complex/hypothesis query
  → optional Planner → parallel deterministic engines
  → evidence reconciliation → Reasoner → deterministic Lead Ranking → Reporter
```

The engine registry includes SQL Retrieval, Search/Ranking, Graph Intelligence, Pattern Analysis, Behavioral Profiling, Financial Analysis, Forecasting, Timeline, and Evidence/Explainability. The evidence gate validates citations, numbers, permissions, contradictions, confidence, and missing evidence. Exact lookups do not call an LLM. Any scale, latency, quality, or cost figure in this document is a design target pending measured validation.

## 2. Deployment Topology

### Catalyst Functions (planned Python Functions)

| Category | Count | Purpose | Trigger |
|----------|-------|---------|---------|
| API/BFF handlers | Planned | Capability/resource REST handlers; run lifecycle and SSE streams | HTTP (API Gateway) |
| Orchestration | 1 state machine + 3 reasoning stages | Planner (optional), Reasoner, Reporter; deterministic engines compute facts | Internal invocation |
| Intelligence Jobs | 6 | Pre-computation engines | Cron (scheduled) |
| Signal Handlers | 7 | Event-driven processors | Signals (data events) |
| Internal typed tools | T01–T23 | Investigation capabilities; not public routes | Orchestrator control |
| Circuit Steps | 4 | Multi-step workflows | Circuits (workflow) |

**Runtime Configuration:**
- Language: Python 3.11
- Memory: 128MB–512MB per function (tier-dependent)
- Timeout: 30s (API), 300s (intelligence jobs), 60s (signal handlers)
- Concurrency: Auto-scaled by Catalyst platform
- Dependencies: LangGraph, LiteLLM, neo4j-driver, onnxruntime, numpy

### AppSail (Neo4j Container)

```
┌──────────────────────────────────────────────┐
│  AppSail Container — Neo4j 5.x               │
│                                              │
│  Memory: 512MB allocated                     │
│  Plugins: GDS (Graph Data Science)           │
│           APOC (utilities)                   │
│                                              │
│  Ports:                                      │
│    7474 — HTTP (Neo4j Browser, disabled prod)│
│    7687 — Bolt (application connections)     │
│                                              │
│  Volumes:                                    │
│    /data    — Graph database files           │
│    /plugins — GDS + APOC JARs               │
│    /conf    — neo4j.conf (tuned)            │
│                                              │
│  Heap: 256MB | Page Cache: 128MB            │
│  Max connections: 50                         │
└──────────────────────────────────────────────┘
```

**Neo4j Configuration Highlights:**
- `dbms.memory.heap.max_size=256m`
- `dbms.memory.pagecache.size=128m`
- `dbms.connector.bolt.listen_address=:7687`
- `dbms.security.procedures.unrestricted=gds.*,apoc.*`
- `dbms.security.procedures.allowlist=gds.*,apoc.*`

### Catalyst AppSail (Frontend)

```
┌──────────────────────────────────────────────┐
│  AppSail — Next.js Web Application           │
│                                              │
│  Framework: Next.js 15 App Router            │
│  Runtime: React 19 + TypeScript              │
│  Hosting: Catalyst AppSail                   │
│  Styling: Tailwind CSS v4 + shadcn/ui        │
│  Primitives: Radix UI + Lucide React         │
│  Motion: Motion (Framer Motion)              │
│  Data: TanStack Query v5 + Zustand            │
│  Forms: React Hook Form + Zod                 │
│  Tables: TanStack Table                       │
│  Visualization: Cytoscape.js, Apache ECharts,│
│                 MapLibre GL                   │
│  Layout: react-resizable-panels              │
│  Interaction: cmdk, Sonner, React DnD         │
│  Content: react-markdown + React PDF          │
│  Theme: next-themes                           │
│  Architecture: Feature-Sliced Design         │
│  Communication: REST + SSE + JWT/Catalyst Auth│
└──────────────────────────────────────────────┘
```

The frontend source tree is rooted at `client/src/` and follows FSD: `app/`, `features/`, `entities/`, `widgets/`, `shared/` (`ui`, `api`, `hooks`, `lib`, `types`, `utils`), and `styles/`. It is deployed on Catalyst AppSail; this frontend deployment choice does not change the Python Catalyst Functions or any backend service.

### Managed Services (Catalyst Platform)

| Service | Role | Configuration |
|---------|------|---------------|
| **Data Store** | Relational storage (FIRs, users, logs) | 2GB free tier, ZCQL interface |
| **Cache** | Key-value caching (L2) | Segment-based, TTL configurable |
| **Stratus** | File/object storage | Pre-computed JSON, ONNX models, reports |
| **Signals** | Event bus (data change triggers) | Row insert/update/delete hooks |
| **Circuits** | Multi-step workflow orchestration | Sequential + parallel steps |
| **Cron** | Scheduled job execution | Daily intelligence refresh, hourly cache warm |
| **Auth** | User authentication & session | JWT tokens, role-based access |
| **API Gateway** | Request routing & rate limiting | Path-based routing, CORS, throttling |
| **SmartBrowz** | Headless browser (web scraping) | OSINT tool for public data extraction |

---

## 3. Data Flow

### Flow 1: Interactive Query (User → AI Response)

```
┌──────┐    ┌───────────┐    ┌──────┐    ┌──────────┐    ┌──────────┐    ┌───────┐
│ User │───▶│API Gateway│───▶│ Auth │───▶│ API Fn   │───▶│LangGraph │───▶│ Tools │
│      │    │           │    │Check │    │(handler) │    │(orchestr)│    │(23)   │
└──────┘    └───────────┘    └──────┘    └──────────┘    └──────────┘    └───┬───┘
                                                                              │
    ┌─────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Tool Execution (parallel via asyncio.gather)                                 │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ Graph Query │  │Vector Search│  │ ZCQL Query  │  │ ONNX Inference  │   │
│  │ (Neo4j/Bolt)│  │(embeddings) │  │(Data Store) │  │ (risk scoring)  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘   │
│         │                │                │                   │            │
│         └────────────────┴────────────────┴───────────────────┘            │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │ Aggregated context
                                     ▼
                              ┌──────────────┐
                              │  LLM Call    │
                              │  (Groq/      │
                              │   Gemini/    │     SSE Stream
                              │   Mistral)   │─────────────────▶ Frontend
                              └──────────────┘                   (real-time
                                                                  token display)
```

**Detailed Steps:**
1. User submits query via chat interface
2. API Gateway routes to appropriate Function endpoint
3. Catalyst Auth validates JWT, extracts user role + permissions
4. API Function initializes LangGraph with user context + conversation history
5. LangGraph orchestrator analyzes intent and routes to reasoning stages and deterministic engines
6. The orchestrator invokes typed tools backed by deterministic engines (parallel where permitted; measure actual concurrency)
7. Tools execute queries across Neo4j, Data Store, Vector index
8. Results aggregated into structured context window
9. LLM synthesizes response with citations
10. Response streamed via SSE (Server-Sent Events) to frontend
11. Audit log entry created asynchronously via Signal

### Flow 2: FIR Ingestion (New Data → Intelligence Update)

```
┌────────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────────┐
│  New FIR   │───▶│  Signal  │───▶│   Entity     │───▶│  Embedding   │
│  (insert)  │    │ (trigger)│    │ Extraction   │    │ Generation   │
└────────────┘    └──────────┘    └──────────────┘    └──────┬───────┘
                                                              │
    ┌─────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐
│ Graph Update │───▶│ Intelligence │───▶│  Alert Check │───▶│  Notify   │
│ (Neo4j)      │    │   Refresh    │    │ (thresholds) │    │  (if hit) │
│              │    │ (affected    │    │              │    │           │
│ • Add nodes  │    │  entities)   │    │ • New links  │    │ • In-app  │
│ • Add edges  │    │              │    │ • Risk spike │    │ • Push    │
│ • Update emb │    │ • Recalc     │    │ • Pattern   │    │           │
└──────────────┘    │   scores     │    │   match     │    └───────────┘
                    └──────────────┘    └──────────────┘
```

**Detailed Steps:**
1. New FIR record inserted into Data Store (manual entry or bulk import)
2. Signal fires on `fir_records` table INSERT event
3. Signal handler Function invoked with row data
4. Entity extraction (NER via ONNX model): persons, locations, vehicles, weapons, organizations
5. Embeddings generated for FIR narrative text (sentence-transformers via ONNX)
6. Neo4j updated: new entity nodes created, relationships established, embeddings stored
7. Affected entity intelligence scores recalculated (criminal network centrality, risk)
8. Alert thresholds checked: new cross-case links, risk score spikes, pattern matches
9. If thresholds breached: notification pushed to relevant officers (SHO, IO)
10. Intelligence cards marked stale → next access triggers refresh or Cron pre-computes

### Flow 3: Daily Intelligence Pre-computation (Cron → Cache Warm)

```
┌──────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌───────────┐
│  Daily   │───▶│  Intelligence    │───▶│  Pre-compute     │───▶│  Store    │
│  Cron    │    │  Engines (6)     │    │  JSON Cards      │    │           │
│  (2 AM)  │    │                  │    │                  │    │ • Stratus │
└──────────┘    │ • Network anal.  │    │ • Entity profiles│    │ • Cache   │
                │ • Community det. │    │ • Hotspot maps   │    │           │
                │ • Temporal patt. │    │ • Network graphs │    └───────────┘
                │ • Risk scoring   │    │ • Risk rankings  │
                │ • Hotspot anal.  │    │ • Trend data     │
                │ • Link predict.  │    │                  │
                └──────────────────┘    └──────────────────┘
```

**Detailed Steps:**
1. Cron triggers at 02:00 IST daily (low-traffic window)
2. Intelligence engine Functions invoked sequentially (resource management)
3. Each engine runs graph algorithms (GDS) and statistical analysis
4. Results serialized as JSON intelligence cards
5. Cards uploaded to Stratus (persistent) + written to Cache (fast access)
6. Stale markers cleared on affected entities
7. Summary statistics updated in Data Store
8. Completion logged; any failures trigger retry with exponential backoff

---

## 4. Performance Architecture

### Latency Targets (design targets pending benchmark)

| Operation | Acceptance target (P99, pending benchmark) | Strategy |
|-----------|-------------|----------|
| Vector retrieval | Design target; measure | Pre-computed BGE-M3 embeddings + pgvector HNSW in Catalyst Data Store |
| Graph traversal | Design target; measure | Indexed properties, bounded depth, cached subgraphs |
| LLM first token | Design target; measure | Groq Llama 3.3 70B with streaming |
| Intelligence card | Design target; measure | Pre-computed JSON from Cache/Stratus |
| Full query response | Design target; measure | Parallel tool execution + streaming |
| FIR search (ZCQL) | Design target; measure | Indexed columns, query optimization |
| Entity resolution | Design target; measure | ONNX model (in-process, no network hop) |

### Caching Architecture (3-Layer)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHING LAYERS                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  L1: In-Memory (per Function instance)                   │    │
│  │                                                          │    │
│  │  • Python dict / lru_cache                              │    │
│  │  • Lifetime: Single invocation (cold start = miss)      │    │
│  │  • Use: LLM prompt templates, config, model weights     │    │
│  │  • Size: <50MB per function                             │    │
│  │  • TTL: Function lifetime (warm instances reuse)        │    │
│  └─────────────────────────────┬───────────────────────────┘    │
│                                │ miss                            │
│  ┌─────────────────────────────▼───────────────────────────┐    │
│  │  L2: Catalyst Cache (shared key-value store)             │    │
│  │                                                          │    │
│  │  • Segment-based organization                           │    │
│  │  • Lifetime: Persistent (TTL-controlled)                │    │
│  │  • Use: Query results, graph snapshots, session state   │    │
│  │  • TTL: 5min (queries), 1hr (graph), 24hr (intel)      │    │
│  │  • Invalidation: Signal-driven on data changes          │    │
│  └─────────────────────────────┬───────────────────────────┘    │
│                                │ miss                            │
│  ┌─────────────────────────────▼───────────────────────────┐    │
│  │  L3: Stratus (pre-computed JSON files)                   │    │
│  │                                                          │    │
│  │  • File-based storage (Catalyst managed)                │    │
│  │  • Lifetime: Until next Cron refresh                    │    │
│  │  • Use: Intelligence cards, entity profiles, reports    │    │
│  │  • Refresh: Daily Cron (02:00 IST)                     │    │
│  │  • Format: Compressed JSON (gzip)                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Cache Key Strategy

```python
# Pattern: {service}:{entity_type}:{identifier}:{version}
CACHE_KEYS = {
    "entity_profile":   "intel:entity:{entity_id}:v{hash}",
    "graph_neighbors":  "graph:neighbors:{node_id}:depth{n}",
    "search_results":   "search:{query_hash}:role{role}",
    "intelligence":     "intel:card:{card_type}:{scope_id}",
    "session_state":    "session:{user_id}:{conversation_id}",
}
```

### Parallel Execution Strategy

```python
# Multi-tool parallel execution via asyncio
async def execute_tools(tools: list[ToolCall]) -> list[ToolResult]:
    """Execute independent tools in parallel, dependent tools sequentially."""
    
    # Group by dependency
    independent = [t for t in tools if not t.depends_on]
    dependent = [t for t in tools if t.depends_on]
    
    # Parallel execution for independent tools
    results = await asyncio.gather(
        *[execute_single_tool(t) for t in independent],
        return_exceptions=True
    )
    
    # Sequential for dependent tools
    for tool in dependent:
        dep_result = next(r for r in results if r.tool_id == tool.depends_on)
        result = await execute_single_tool(tool, context=dep_result)
        results.append(result)
    
    return results
```

### SSE Streaming Architecture

```
Frontend (EventSource)          Backend (Function)
      │                              │
      │◀─── event: token ───────────│  (LLM generates token)
      │◀─── event: token ───────────│  (next token)
      │◀─── event: tool_start ──────│  (tool invoked)
      │◀─── event: tool_result ─────│  (tool completed)
      │◀─── event: token ───────────│  (synthesis continues)
      │◀─── event: citation ────────│  (source reference)
      │◀─── event: done ────────────│  (stream complete)
      │                              │
```

**SSE Event Types:**
- `token` — Individual LLM output token for real-time display
- `tool_start` — Tool invocation begun (shows loading indicator)
- `tool_result` — Tool completed with summary (expandable in UI)
- `citation` — Source reference for response grounding
- `error` — Recoverable error with context
- `done` — Stream complete, includes metadata (tokens used, latency)

---

## 5. Security Architecture

### Authentication (Catalyst Auth)

```
┌──────────┐     ┌────────────┐     ┌──────────────┐     ┌──────────┐
│  Login   │────▶│ Catalyst   │────▶│  JWT Token   │────▶│ Session  │
│  (creds) │     │ Auth       │     │  (signed)    │     │ Created  │
└──────────┘     └────────────┘     └──────────────┘     └──────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │  Token       │
                                    │  Contents:   │
                                    │  • user_id   │
                                    │  • role      │
                                    │  • station   │
                                    │  • exp_time  │
                                    │  • perms[]   │
                                    └──────────────┘
```

**Auth Flow:**
1. User submits credentials (username + password)
2. Catalyst Auth validates against user store
3. JWT issued with role, station, and permission claims
4. Session created in Catalyst (server-side state)
5. Token returned to frontend, stored in httpOnly cookie
6. Subsequent requests include token in Authorization header
7. API Gateway validates token before Function invocation
8. Function receives verified user context (no re-validation needed)

### Role-Based Access Control (RBAC)

| Role | Code | Access Level | Permissions |
|------|------|-------------|-------------|
| **Station House Officer** | SHO | Station-wide | View all FIRs (own station), assign IOs, view intelligence, manage station users |
| **Investigation Officer** | IO | Case-specific | View assigned FIRs, run queries, use AI tools, update case notes |
| **Deputy Commissioner** | DCP | District-wide | View all stations in district, cross-station intelligence, analytics dashboard |
| **Crime Analyst** | Analyst | Cross-cutting | Full intelligence access, pattern analysis, no case modification |
| **Superintendent** | SP | State-wide | All access, system configuration, audit review, user management |

**Permission Matrix:**

```
┌───────────────────────────┬─────┬─────┬─────┬─────────┬─────┐
│ Permission                │ SHO │ IO  │ DCP │ Analyst │ SP  │
├───────────────────────────┼─────┼─────┼─────┼─────────┼─────┤
│ View FIRs (own station)   │  ✓  │  ✓* │  ✓  │    ✓    │  ✓  │
│ View FIRs (other station) │  ✗  │  ✗  │  ✓  │    ✓    │  ✓  │
│ Modify FIR                │  ✓  │  ✓* │  ✗  │    ✗    │  ✓  │
│ AI Chat (investigation)   │  ✓  │  ✓  │  ✓  │    ✓    │  ✓  │
│ Intelligence Cards        │  ✓  │  ✓  │  ✓  │    ✓    │  ✓  │
│ Cross-case Network View   │  ✗  │  ✗  │  ✓  │    ✓    │  ✓  │
│ Pattern Analysis           │  ✗  │  ✗  │  ✓  │    ✓    │  ✓  │
│ User Management           │  ✓† │  ✗  │  ✓† │    ✗    │  ✓  │
│ Audit Log Access          │  ✗  │  ✗  │  ✓  │    ✗    │  ✓  │
│ System Configuration      │  ✗  │  ✗  │  ✗  │    ✗    │  ✓  │
│ Export Data               │  ✗  │  ✗  │  ✓  │    ✓    │  ✓  │
│ OSINT Tools               │  ✗  │  ✓  │  ✗  │    ✓    │  ✓  │
├───────────────────────────┴─────┴─────┴─────┴─────────┴─────┤
│ * IO: Only assigned cases  † Limited to own scope            │
└──────────────────────────────────────────────────────────────┘
```

### Audit Trail (Immutable Hash-Chained Log)

```
┌──────────────────────────────────────────────────────────────────┐
│  AUDIT LOG ENTRY                                                  │
│                                                                   │
│  {                                                                │
│    "log_id": "uuid-v4",                                          │
│    "timestamp": "ISO-8601",                                      │
│    "user_id": "officer-id",                                      │
│    "action": "query|view|modify|export|login|admin",             │
│    "resource": "fir|entity|intelligence|system",                 │
│    "resource_id": "specific-record-id",                          │
│    "details": { /* action-specific metadata */ },                │
│    "ip_address": "x.x.x.x",                                     │
│    "session_id": "session-ref",                                  │
│    "prev_hash": "sha256-of-previous-entry",                     │
│    "entry_hash": "sha256(prev_hash + payload)"                  │
│  }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Hash Chain Mechanism:**
```python
import hashlib, json

def create_audit_entry(action: dict, prev_hash: str) -> dict:
    """Create tamper-evident audit log entry."""
    payload = json.dumps(action, sort_keys=True)
    entry_hash = hashlib.sha256(
        f"{prev_hash}:{payload}".encode()
    ).hexdigest()
    return {**action, "prev_hash": prev_hash, "entry_hash": entry_hash}
```

- Stored via Signals (event-driven, non-blocking)
- Chain integrity verified on audit review
- Any tampering detected by hash mismatch
- Retention: Indefinite (compliance requirement)

### Data Protection

| Layer | Mechanism | Details |
|-------|-----------|---------|
| **At Rest** | Catalyst-managed encryption | AES-256, platform-managed keys |
| **In Transit** | TLS 1.3 | All connections (API, Bolt, internal) |
| **Application** | Field-level sensitivity | PII fields marked, access-logged |
| **Backup** | Encrypted snapshots | Daily automated backups (Catalyst) |

### PII & Data Handling Policy

```
┌─────────────────────────────────────────────────────────┐
│  DATA CLASSIFICATION                                     │
│                                                          │
│  SYNTHETIC ONLY (Hackathon/Demo):                       │
│  • All FIR data is synthetically generated               │
│  • Names, locations, phone numbers are fictional         │
│  • Patterns modeled on real crime statistics (public)    │
│                                                          │
│  IF REAL DATA (Future Production):                       │
│  • Anonymization pipeline before ingestion               │
│  • K-anonymity (k≥5) for demographic attributes         │
│  • Location fuzzing (±500m for addresses)               │
│  • Name tokenization (reversible only with master key)  │
│  • Audit log for every PII access                       │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Scalability

### Design Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| FIR Records | 50,000 | 5 years × 10K FIRs/year (medium district) |
| Entity Nodes | 200,000 | ~4 entities per FIR average |
| Relationships | 500,000 | ~2.5 relationships per entity |
| Concurrent Users | 50 | Peak usage (shift change overlap) |
| Daily Queries | 5,000 | ~100 queries per active officer per day |
| Intelligence Cards | 10,000 | Pre-computed for top entities + hotspots |

### Auto-Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│  SCALING ARCHITECTURE                                            │
│                                                                  │
│  Catalyst Functions (Serverless)                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  • Auto-scaled by platform (no configuration needed)     │    │
│  │  • Cold start: design estimate; measure on Catalyst     │    │
│  │  • Warm instances reused for subsequent requests         │    │
│  │  • Concurrency: Platform-managed (burst capable)        │    │
│  │  • Strategy: Keep functions lean, offload state          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  AppSail — Neo4j (Container)                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  • Base: 1 instance (512MB) — handles 50 concurrent     │    │
│  │  • Scale-up: Up to 5 instances via AppSail              │    │
│  │  • Read replicas: If read-heavy patterns emerge         │    │
│  │  • Connection pooling: 50 connections per instance      │    │
│  │  • Index strategy: All queried properties indexed       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Data Store (Managed)                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  • Free tier: 2GB storage                               │    │
│  │  • Growth: Credits-based expansion                      │    │
│  │  • Partitioning: By station_id (locality)               │    │
│  │  • Archival: Old FIRs (>5yr) → Stratus JSON export     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Capacity Planning

```
Storage Budget (Free Tier):
├── Data Store: 2GB
│   ├── fir_records:     ~800MB (50K × 16KB avg)
│   ├── entities:        ~200MB (200K × 1KB)
│   ├── audit_logs:      ~500MB (high volume, append-only)
│   ├── users/config:    ~10MB
│   └── headroom:        ~490MB
│
├── Neo4j (AppSail disk): 512MB
│   ├── Graph data:      ~200MB (nodes + relationships)
│   ├── Indexes:         ~100MB (property + fulltext + vector)
│   ├── Transaction logs: ~100MB (rotating)
│   └── Headroom:        ~112MB
│
├── Stratus: Generous (file storage)
│   ├── Intelligence JSON: ~50MB (10K cards × 5KB)
│   ├── ONNX models:      ~100MB (NER + embeddings)
│   ├── Reports:           ~50MB (generated PDFs)
│   └── Backups:           ~200MB (graph exports)
│
└── Cache: Segment-based
    ├── Active queries:    ~50MB
    ├── Intelligence:      ~20MB (hot cards)
    └── Sessions:          ~10MB
```

### Growth Strategy

| Phase | FIRs | Action |
|-------|------|--------|
| Hackathon | 500 (synthetic) | Single instance, no optimization needed |
| Pilot | Initial sizing estimate; validate | Basic indexing, daily pre-computation |
| District | Initial sizing estimate; validate | Full caching, Catalyst capacity validation |
| State | 500,000+ (future) | Sharding, dedicated infrastructure, paid tier |

---

## 7. Monitoring & Observability

### Monitoring Stack

```
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVABILITY ARCHITECTURE                                      │
│                                                                  │
│  ┌───────────────────────────────────────────────────┐          │
│  │  Catalyst Built-in Monitoring                      │          │
│  │                                                    │          │
│  │  • Function invocations (count, duration, errors) │          │
│  │  • AppSail container health (CPU, memory, restarts│          │
│  │  • Data Store operations (queries/sec, latency)   │          │
│  │  • Cache hit/miss ratios                          │          │
│  │  • API Gateway request volume & error rates       │          │
│  └───────────────────────────────────────────────────┘          │
│                                                                  │
│  ┌───────────────────────────────────────────────────┐          │
│  │  Custom Application Monitoring                     │          │
│  │                                                    │          │
│  │  ┌─────────────────────────────────────────────┐  │          │
│  │  │  LangGraph Trace Logger                      │  │          │
│  │  │                                              │  │          │
│  │  │  • Orchestrator routing decisions                   │  │          │
│  │  │  • Tool invocations + latency               │  │          │
│  │  │  • LLM token usage (per model)              │  │          │
│  │  │  • Context window utilization               │  │          │
│  │  │  • Error recovery actions                    │  │          │
│  │  │                                              │  │          │
│  │  │  Storage: audit_logs table (Data Store)     │  │          │
│  │  └─────────────────────────────────────────────┘  │          │
│  │                                                    │          │
│  │  ┌─────────────────────────────────────────────┐  │          │
│  │  │  Intelligence Pipeline Monitor               │  │          │
│  │  │                                              │  │          │
│  │  │  • Cron job completion status                │  │          │
│  │  │  • Pre-computation duration                  │  │          │
│  │  │  • Cards generated/refreshed count          │  │          │
│  │  │  • Graph algorithm execution time            │  │          │
│  │  │  • Signal processing lag                     │  │          │
│  │  └─────────────────────────────────────────────┘  │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Metrics & Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Function error rate | >5% | >15% | Alert → investigate logs |
| LLM latency (P95) | Initial alert threshold; validate | Initial escalation threshold; validate | Switch to faster model / reduce context |
| Neo4j query time | Initial alert threshold; validate | Initial escalation threshold; validate | Check query plan, add indexes |
| Cache hit ratio | Initial warning threshold; validate | Initial critical threshold; validate | Review TTL, pre-warm strategy |
| Daily API calls | >80% free tier | >90% free tier | Budget alert email |
| AppSail memory | >80% (410MB) | >90% (460MB) | Restart / tune heap |
| Data Store usage | >70% (1.4GB) | >85% (1.7GB) | Archive old data |
| Cron job duration | >10min | >30min | Optimize algorithms |

### Alert Configuration

```python
# Budget monitoring (runs hourly via Cron)
ALERT_THRESHOLDS = {
    "catalyst_functions": {
        "free_tier_limit": 25000,  # invocations/day
        "warning_pct": 0.80,
        "critical_pct": 0.90,
    },
    "data_store": {
        "free_tier_limit_mb": 2048,
        "warning_pct": 0.70,
        "critical_pct": 0.85,
    },
    "llm_tokens": {
        "daily_budget": 1_000_000,  # tokens across all models
        "warning_pct": 0.80,
        "critical_pct": 0.90,
    },
}

# Alert channels
ALERT_CHANNELS = {
    "email": ["admin@ksp-investigateai.catalyst.com"],
    "in_app": True,  # Dashboard notification
}
```

### Trace Logging Schema

```json
{
  "trace_id": "uuid-v4",
  "session_id": "conversation-ref",
  "timestamp": "2026-07-23T08:30:00Z",
  "user_id": "officer-123",
  "query": "Find connections between suspect X and Y",
  "agent_path": ["supervisor", "network_analyst", "graph_tool"],
  "tools_invoked": [
    {"name": "graph_traverse", "latency_ms": 87, "results": 12},
    {"name": "vector_search", "latency_ms": 145, "results": 5}
  ],
  "llm_calls": [
    {"model": "groq/llama-3.3-70b-versatile", "tokens_in": 2400, "tokens_out": 580, "latency_ms": 1200}
  ],
  "total_latency_ms": 2100,
  "cache_hits": 3,
  "cache_misses": 1,
  "error": null
}
```

---

## 8. Project Structure

```
ksp-investigate-ai/
│
├── catalyst.json                    # Catalyst project configuration
├── catalyst-ci.yaml                 # CI/CD pipeline definition
├── README.md                        # Project overview & setup guide
├── .env.example                     # Environment variable template
│
├── functions/                       # All Catalyst Functions (Python 3.11)
│   │
│   ├── api/                         # Catalyst API Gateway REST handlers
│   │   ├── investigation_runs.py    # POST /api/v1/investigations/{id}/runs; run lifecycle
│   │   ├── capability_api.py        # POST capability routes (query, network, profile, similar, hypothesis, report)
│   │   ├── resource_api.py          # Resource REST for investigations, evidence, timeline, notes, reports
│   │   ├── sse_api.py               # GET /api/v1/runs/{run_id}/events; cookie/fetch-authenticated SSE
│   │   ├── upload_api.py            # Multipart voice/audio and document uploads
│   │   └── alert_api.py             # Alert resources and SSE alert lifecycle
│   │
│   ├── orchestration/                # LangGraph state machine + reasoning stages (internal)
│   │   ├── orchestrator.py          # LangGraph state machine; routing/checkpoints/SSE
│   │   ├── planner_stage.py         # Optional ambiguity/complexity planning
│   │   ├── reasoner_stage.py        # Grounded synthesis and hypothesis evaluation
│   │   └── reporter_stage.py        # Evidence-gated communication and report wording
│   │
│   ├── engines/                     # Deterministic computation modules
│   │   ├── sql_retrieval.py         # Structured retrieval and aggregates
│   │   ├── search_ranking.py        # Vector/BM25/RRF/reranking
│   │   ├── graph_intelligence.py    # Traversal, paths, communities, centrality
│   │   ├── pattern_analysis.py      # MO, anomalies, temporal patterns
│   │   ├── behavioral_profiling.py  # Profile features and review signals
│   │   ├── financial_analysis.py    # Account flows and transaction indicators
│   │   ├── forecasting.py           # Forecasts and uncertainty
│   │   ├── timeline.py              # Chronology and gap detection
│   │   ├── lead_ranking.py          # Deterministic lead ranking
│   │   └── evidence.py              # Citations, permissions, contradictions, confidence
│   │
│   ├── intelligence/                # Cron-triggered Intelligence Jobs (6 functions)
│   │   ├── network_analysis.py      #   Community detection & centrality
│   │   ├── temporal_patterns.py     #   Time-series crime patterns
│   │   ├── hotspot_detection.py     #   Geographic clustering
│   │   ├── risk_scoring.py          #   Entity risk computation
│   │   ├── link_prediction.py       #   Predicted future connections
│   │   └── trend_computation.py     #   Statistical trend analysis
│   │
│   ├── signals/                     # Event-driven Handlers (7 functions)
│   │   ├── fir_ingestion.py         #   New FIR → entity extraction pipeline
│   │   ├── entity_embedding.py      #   Entity created → generate embedding
│   │   ├── graph_sync.py            #   Entity/relation → Neo4j sync
│   │   ├── cache_invalidation.py    #   Data change → invalidate affected cache
│   │   ├── alert_generator.py       #   Threshold breach → notification
│   │   ├── audit_logger.py          #   Any action → hash-chained log entry
│   │   └── intelligence_refresh.py  #   Entity update → mark cards stale
│   │
│   ├── registry/                    # Internal typed T01–T23 tool registry
│   │   ├── schemas.py               # Pydantic inputs/outputs and authorization context
│   │   ├── dispatch.py               # Tool-to-engine dispatch and audit metadata
│   │   └── tools.py                  # T01–T23 definitions; not public routes
│   │
│   ├── circuits/                    # Workflow Steps (4 functions)
│   │   ├── bulk_ingest_step.py      #   Batch FIR processing
│   │   ├── quality_check_step.py    #   Data validation & enrichment
│   │   ├── graph_build_step.py      #   Graph construction from entities
│   │   └── index_build_step.py      #   Vector index construction
│   │
│   ├── shared/                      # Shared utilities
│   │   ├── config.py                #   Environment & configuration
│   │   ├── auth_middleware.py       #   Permission checking decorators
│   │   ├── cache_utils.py           #   L1/L2/L3 cache operations
│   │   ├── neo4j_client.py          #   Neo4j connection pool
│   │   ├── llm_client.py            #   LiteLLM wrapper with fallback
│   │   ├── embedding_utils.py       #   ONNX embedding generation
│   │   ├── audit_utils.py           #   Hash-chain audit logging
│   │   └── error_handler.py         #   Standardized error responses
│   │
│   └── requirements.txt             # Python dependencies (pinned)
│
├── appsail/                         # AppSail Container Configuration
│   └── neo4j/
│       ├── Dockerfile               #   Neo4j 5.x + GDS + APOC
│       ├── neo4j.conf               #   Tuned configuration (512MB)
│       ├── plugins/
│       │   ├── neo4j-graph-data-science-*.jar
│       │   └── apoc-*-core.jar
│       ├── import/                   #   Initial data import scripts
│       │   └── schema.cypher        #   Indexes & constraints
│       └── scripts/
│           ├── init.sh              #   Container initialization
│           └── health-check.sh      #   Liveness probe
│
├── client/                          # Next.js 15 + React 19 frontend on AppSail
│   ├── package.json                 # Pinned frontend dependencies
│   ├── next.config.ts               # Next.js App Router configuration
│   ├── tsconfig.json
│   ├── postcss.config.mjs           # Tailwind CSS v4
│   └── src/                         # Feature-Sliced Design root
│       ├── app/                     # Routes, layouts, providers
│       ├── features/
│       │   ├── investigation/      # Lifecycle, health, workspace state
│       │   ├── evidence/            # Evidence board and provenance
│       │   ├── graph/               # Cytoscape.js graph interactions
│       │   ├── intelligence/        # Card dock, confidence, freshness
│       │   ├── timeline/            # Timeline and gaps
│       │   ├── reports/             # Report preview/export
│       │   ├── chat/                # Conversation and SSE streaming
│       │   └── authentication/     # JWT/Catalyst Authentication UI
│       ├── entities/                # Domain-shaped frontend models
│       ├── widgets/                 # Seven-panel workspace composition
│       ├── shared/
│       │   ├── ui/                  # shadcn/ui, Radix UI, Lucide React
│       │   ├── api/                 # REST and SSE clients
│       │   ├── hooks/               # Shared hooks
│       │   ├── lib/                 # Query, theme, DnD, and setup utilities
│       │   ├── types/               # TypeScript view/API types
│       │   └── utils/               # Pure frontend utilities
│       └── styles/                  # Tailwind v4 theme and global styles
│
├── data/                            # Synthetic Data Generation
│   ├── generator/
│   │   ├── fir_generator.py         #   Generate realistic FIRs
│   │   ├── entity_generator.py      #   Generate persons, vehicles, etc.
│   │   ├── network_generator.py     #   Generate criminal networks
│   │   └── karnataka_context.py     #   Karnataka-specific names, places
│   ├── seed/
│   │   ├── ipc_sections.json        #   IPC/BNS section definitions
│   │   ├── stations.json            #   KSP station hierarchy
│   │   └── templates.json           #   FIR narrative templates
│   └── output/                      #   Generated synthetic datasets
│
├── .LOCK/                           # Architecture Documentation
│   ├── architecture.md              #   THIS FILE — System architecture
│   ├── data-model.md                #   Graph & relational schema
│   ├── orchestration-design.md       #   LangGraph orchestrator and reasoning stages
│   ├── api-spec.md                  #   REST API specification
│   └── deployment.md                #   Deployment & operations guide
│
├── tests/                           # Test Suite
│   ├── unit/                        #   Unit tests (pytest)
│   ├── integration/                 #   Integration tests
│   └── e2e/                         #   End-to-end tests
│
└── docs/                            # User-facing Documentation
    ├── setup.md                     #   Development setup guide
    ├── user-guide.md                #   End-user documentation
    └── api-reference.md             #   API documentation
```

---

## 9. Integration Points

### Integration Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTEGRATION TOPOLOGY                                   │
│                                                                              │
│                         ┌──────────────┐                                     │
│                         │   Frontend   │                                     │
│                         │  (Next.js 15 App Router) │                          │
│                         └──────┬───────┘                                     │
│                                │                                             │
│                    ┌───────────┴───────────┐                                 │
│                    │ REST capability/resource APIs + SSE │                                  │
│                    ▼                ▼      │                                  │
│           ┌──────────────┐  ┌──────────────┐                                │
│           │  API Calls   │  │   Streaming  │                                │
│           │  (JSON)      │  │   (tokens)   │                                │
│           └──────┬───────┘  └──────┬───────┘                                │
│                  │                  │                                         │
│                  └────────┬─────────┘                                        │
│                           │                                                  │
│                    ┌──────▼───────┐                                          │
│                    │  Functions   │                                           │
│                    │  (Python)    │                                           │
│                    └──────┬───────┘                                          │
│                           │                                                  │
│      ┌────────┬───────────┼───────────┬─────────┬──────────┐               │
│      │        │           │           │         │          │               │
│      ▼        ▼           ▼           ▼         ▼          ▼               │
│  ┌───────┐┌───────┐ ┌────────┐ ┌─────────┐┌────────┐┌─────────┐          │
│  │ Neo4j ││DataStr││ LLMs   │ │ Stratus ││ Cache  ││  ONNX   │          │
│  │(Bolt) ││(ZCQL) ││(HTTPS) │ │ (SDK)   ││ (SDK)  ││(in-proc)│          │
│  └───────┘└───────┘ └────────┘ └─────────┘└────────┘└─────────┘          │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │  Event-Driven Integrations                                    │           │
│  │                                                               │           │
│  │  Signals ──▶ Functions (data change events)                  │           │
│  │  Cron    ──▶ Functions (scheduled triggers)                  │           │
│  │  Circuits──▶ Functions (workflow step invocation)             │           │
│  └──────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Integration Specifications

#### 1. Frontend ↔ Capability API / BFF (REST + SSE + Multipart)

The external boundary uses Catalyst API Gateway for authentication, RBAC, throttling, and routing. REST APIs are capability-oriented for investigation actions and resource-oriented for workspace state. Complex investigations create a run with REST and stream progress through SSE; simple lookups may return synchronously. Voice and document inputs use multipart REST.

Catalyst API Gateway exposes capability-oriented and resource REST routes; the LangGraph engine and its internal typed Python Tool Registry are not public endpoints. The orchestrator and permitted reasoning stages call typed tools; tools enforce authorization context, schemas, query limits, citations, and audit events. WebSockets are deferred until collaborative editing or presence is required. gRPC is reserved for a future split into independent internal services, and MCP is an optional interoperability adapter rather than a runtime dependency.

| Aspect | Detail |
|--------|--------|
| Protocol | HTTPS (TLS 1.3) |
| Format | JSON (request/response), SSE (streaming) |
| Auth | Bearer token (JWT) in Authorization header |
| Base URL | `https://{project}.catalyst.com/api/` |
| Versioning | Path-based (`/api/v1/...`) |
| Error format | `{ "error": { "code": "ERR_XXX", "message": "...", "details": {} } }` |
| Rate limiting | Per-role limits are configuration targets pending Catalyst validation |
| CORS | Catalyst-managed, AppSail frontend domain whitelisted |

**SSE Connection:**
```javascript
// Cookie-authenticated SSE; native EventSource cannot set Authorization headers.
const eventSource = new EventSource(
  `/api/v1/runs/${runId}/events`,
  { withCredentials: true }
);
// If bearer-only auth is required, use a fetch-based SSE client that sends
// Authorization explicitly; do not pass headers to native EventSource.

eventSource.addEventListener('token', (e) => appendToken(e.data));
eventSource.addEventListener('tool_start', (e) => showToolLoading(e.data));
eventSource.addEventListener('tool_result', (e) => showToolResult(e.data));
eventSource.addEventListener('done', (e) => finalizeResponse(e.data));
```

#### 2. Functions ↔ Neo4j (Bolt Protocol)

| Aspect | Detail |
|--------|--------|
| Protocol | Bolt (binary, port 7687) |
| Driver | `neo4j` Python driver (v5.x) |
| Auth | Basic auth (username/password from env) |
| Connection pool | Min: 5, Max: 50 connections |
| Query timeout | 30 seconds |
| Transaction mode | Read (default), Write (mutations only) |

**Connection Pattern:**
```python
from neo4j import AsyncGraphDatabase

class Neo4jClient:
    def __init__(self):
        self._driver = AsyncGraphDatabase.driver(
            uri=os.environ["NEO4J_URI"],       # bolt://appsail-host:7687
            auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
            max_connection_pool_size=50,
            connection_acquisition_timeout=10,
        )
    
    async def read(self, cypher: str, params: dict = None):
        async with self._driver.session(default_access_mode="READ") as session:
            result = await session.run(cypher, params or {})
            return await result.data()
    
    async def write(self, cypher: str, params: dict = None):
        async with self._driver.session(default_access_mode="WRITE") as session:
            result = await session.run(cypher, params or {})
            return await result.data()
```

#### 3. Functions ↔ Data Store (Catalyst SDK / ZCQL)

| Aspect | Detail |
|--------|--------|
| Interface | Catalyst Python SDK |
| Query language | ZCQL (Zoho Catalyst Query Language — SQL-like) |
| Operations | SELECT, INSERT, UPDATE, DELETE |
| Bulk operations | Batch insert (up to 200 rows) |
| Transactions | Single-table atomic operations |

**Usage Pattern:**
```python
import zcatalyst_sdk

def query_firs(station_id: str, date_from: str):
    app = zcatalyst_sdk.initialize()
    zcql = app.zcql()
    
    result = zcql.execute_query(
        f"SELECT * FROM fir_records "
        f"WHERE station_id = '{station_id}' "
        f"AND date_filed >= '{date_from}' "
        f"ORDER BY date_filed DESC LIMIT 100"
    )
    return result
```

#### 4. Functions ↔ LLMs (OpenAI SDK via LiteLLM)

| Aspect | Detail |
|--------|--------|
| Library | LiteLLM (unified interface) |
| Primary model | `groq/llama-3.3-70b-versatile` (primary) |
| Reasoning model | `gemini/gemini-2.5-flash` (secondary) |
| Fallback model | `mistral/mistral-small-latest` (tertiary) |
| Streaming | Enabled (async generator) |
| Max tokens | 4096 (response), 8192 (context window budget) |
| Temperature | 0.1 (factual), 0.4 (analysis), 0.7 (creative summaries) |

**LLM Client with Fallback:**
```python
import litellm
from litellm import acompletion

MODEL_CHAIN = [
    "groq/llama-3.3-70b-versatile", # Primary
    "gemini/gemini-2.5-flash",       # Secondary
    "mistral/mistral-small-latest",  # Tertiary
]

async def llm_call(messages: list, stream: bool = True, **kwargs):
    """Call LLM with automatic fallback chain."""
    for model in MODEL_CHAIN:
        try:
            response = await acompletion(
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )
            return response
        except Exception as e:
            if model == MODEL_CHAIN[-1]:
                raise  # All models failed
            continue  # Try next model
```

#### 5. Functions ↔ ONNX Models (In-Process Inference)

| Aspect | Detail |
|--------|--------|
| Runtime | `onnxruntime` (CPU provider) |
| Models | NER (token classification), Embeddings (sentence-transformers) |
| Loading | Lazy load on first use, cached in L1 memory |
| Storage | Stratus (downloaded to /tmp on cold start) |
| Inference | Synchronous (single-threaded; latency pending benchmark) |

**Inference Pattern:**
```python
import onnxruntime as ort
import numpy as np

class ONNXModel:
    _session = None
    
    @classmethod
    def get_session(cls, model_path: str):
        if cls._session is None:
            cls._session = ort.InferenceSession(
                model_path,
                providers=['CPUExecutionProvider']
            )
        return cls._session
    
    @classmethod
    def embed(cls, text: str) -> np.ndarray:
        session = cls.get_session("/tmp/models/embeddings.onnx")
        tokens = tokenize(text)  # Pre-processing
        outputs = session.run(None, {"input_ids": tokens})
        return outputs[0].mean(axis=1)  # Mean pooling
```

#### 6. Functions ↔ Stratus (File Operations)

| Aspect | Detail |
|--------|--------|
| Interface | Catalyst Python SDK (file store) |
| Operations | Upload, download, list, delete |
| Use cases | Pre-computed JSON, ONNX models, generated reports |
| Naming | `{type}/{entity_id}/{timestamp}.json` |

**Usage Pattern:**
```python
import zcatalyst_sdk
import json

def store_intelligence_card(card_type: str, entity_id: str, data: dict):
    app = zcatalyst_sdk.initialize()
    file_store = app.filestore()
    
    folder = file_store.get_folder(INTELLIGENCE_FOLDER_ID)
    filename = f"{card_type}_{entity_id}.json"
    
    folder.upload_file(
        filename=filename,
        content=json.dumps(data).encode(),
        content_type="application/json"
    )

def get_intelligence_card(card_type: str, entity_id: str) -> dict:
    app = zcatalyst_sdk.initialize()
    file_store = app.filestore()
    
    folder = file_store.get_folder(INTELLIGENCE_FOLDER_ID)
    content = folder.download_file(f"{card_type}_{entity_id}.json")
    return json.loads(content)
```

#### 7. Signals ↔ Functions (Event-Driven)

| Aspect | Detail |
|--------|--------|
| Trigger | Data Store row INSERT/UPDATE/DELETE |
| Payload | Changed row data + operation type |
| Invocation | Asynchronous (non-blocking) |
| Retry | 3 attempts with exponential backoff |
| Ordering | Per-table, not guaranteed cross-table |

**Signal Configuration:**
```json
{
  "signals": [
    {
      "table": "fir_records",
      "operation": "INSERT",
      "function": "fir_ingestion",
      "async": true
    },
    {
      "table": "entities",
      "operation": "INSERT",
      "function": "entity_embedding",
      "async": true
    },
    {
      "table": "entities",
      "operation": "UPDATE",
      "function": "cache_invalidation",
      "async": true
    }
  ]
}
```

#### 8. Cron ↔ Functions (Scheduled)

| Aspect | Detail |
|--------|--------|
| Scheduler | Catalyst Cron |
| Granularity | Minutely, hourly, daily, weekly |
| Timeout | 300 seconds (5 minutes) |
| Concurrency | Sequential (no overlap) |
| Failure | Logged, retried next scheduled slot |

**Cron Schedule:**
```json
{
  "cron_jobs": [
    {
      "name": "daily_intelligence",
      "function": "network_analysis",
      "schedule": "0 2 * * *",
      "description": "Daily intelligence pre-computation (2 AM IST)"
    },
    {
      "name": "hourly_cache_warm",
      "function": "trend_computation",
      "schedule": "0 * * * *",
      "description": "Hourly cache warming for hot entities"
    },
    {
      "name": "budget_monitor",
      "function": "health_api",
      "schedule": "0 */6 * * *",
      "description": "Check resource usage every 6 hours"
    }
  ]
}
```

#### 9. Circuits ↔ Functions (Workflow Steps)

| Aspect | Detail |
|--------|--------|
| Orchestrator | Catalyst Circuits |
| Step types | Sequential, parallel, conditional |
| Data passing | JSON payload between steps |
| Error handling | Per-step retry + circuit-level rollback |
| Use case | Bulk data ingestion pipeline |

**Circuit Definition (Bulk Ingest):**
```
┌────────────────────────────────────────────────────────────────┐
│  CIRCUIT: bulk_fir_ingest                                       │
│                                                                 │
│  Step 1: bulk_ingest_step                                      │
│    Input:  { "file_id": "stratus-file-ref" }                   │
│    Output: { "records": [...parsed FIRs...] }                  │
│                                                                 │
│  Step 2: quality_check_step                                    │
│    Input:  { "records": [...] }                                │
│    Output: { "valid": [...], "invalid": [...] }                │
│                                                                 │
│  Step 3: graph_build_step (parallel with Step 4)               │
│    Input:  { "valid": [...] }                                  │
│    Output: { "nodes_created": N, "edges_created": M }          │
│                                                                 │
│  Step 4: index_build_step (parallel with Step 3)               │
│    Input:  { "valid": [...] }                                  │
│    Output: { "embeddings_generated": N }                       │
│                                                                 │
│  Completion: Intelligence refresh triggered                     │
└────────────────────────────────────────────────────────────────┘
```

---

## Summary

KSP InvestigateAI is a fully serverless, AI-powered criminal investigation platform built on Zoho Catalyst. The architecture prioritizes:

- **Speed**: Pre-computed intelligence + streaming responses for streaming UX; benchmark target pending measurement
- **Intelligence**: LangGraph orchestrator with 23 typed tools backed by deterministic engines and graph intelligence
- **Security**: Role-based access, immutable audit trails, and encryption throughout
- **Cost**: Uses Catalyst free tier where available plus the $250 trial credits; actual cost depends on measured usage
- **Scalability**: From hackathon demo (500 FIRs) to district deployment (50K FIRs) without architecture changes

The system transforms raw FIR data into actionable intelligence through a pipeline of entity extraction, graph construction, algorithmic analysis, and AI-powered reasoning — enabling Karnataka State Police officers to uncover hidden patterns and solve cases faster.

---

*Document generated for KSP InvestigateAI — Catalyst Hackathon 2026*  
*Architecture Version: 1.0.0 | Derived from locked decisions*