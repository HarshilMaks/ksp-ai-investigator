# KSP InvestigateAI — Orchestrator and Deterministic Engine Architecture
> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24


> **Classification**: CORE DIFFERENTIATOR — evidence-grounded orchestration over deterministic intelligence
> **Version**: 1.0.0  
> **Last Updated**: 2026-07-23  
> **Entry Point**: `src/orchestration/orchestrator.py`

---

## Why an Orchestrator, Not a Chatbot

```
❌ Chatbot:    Question → LLM → Answer (single inference, no tools, no memory)
✅ This:       Question → route fast/deep → deterministic engines → evidence gate → cited response/package
```

KSP InvestigateAI deploys one **LangGraph Investigation Orchestrator** with three LLM reasoning stages and deterministic engines. The state machine provides persistent memory, parallel execution, authorization, retries, and conditional routing; the number of parallel engine calls is a design target pending measurement.

---

## Orchestrator and Reasoning Stages

InvestigateAI has one **LangGraph Investigation Orchestrator**. It is a state machine—not an LLM agent—and owns routing, state, checkpointing, retries, parallel fan-out/fan-in, authorization context, and SSE progress. LLM use is limited to three reasoning stages:

| Stage | Invocation | Responsibility | Output boundary |
|---|---|---|---|
| **Planner Agent** | Optional; ambiguity or complexity only | Converts intent into a validated execution plan; never emits unrestricted SQL/Cypher | Typed plan referencing allowed T01–T23 tools |
| **Reasoning Agent** | Deep path after engine results and reconciliation | Grounded synthesis, hypothesis evaluation, contradictions, missing evidence, and structured rationale | Claims linked to evidence; no literal private chain-of-thought |
| **Reporter Agent** | When communication or a package is requested | Wording for summaries, timelines, bilingual responses, and reports | Evidence-gated, human-reviewable report artifacts |

Decision Support is **not an agent**. The deterministic **Lead Ranking Engine** ranks leads from evidence, rules, expected value, freshness, and permissions; an optional LLM explanation may describe the ranking after validation.

### Fast and deep routing

```text
Exact/structured, low-risk query
  → deterministic SQL/Search/Graph/Timeline engine
  → Evidence/Explainability Engine (evidence gate)
  → synchronous cited response; no LLM when unnecessary

Ambiguous, relational, or hypothesis query
  → optional Planner Agent
  → parallel deterministic engines
  → evidence reconciliation and gate
  → Reasoning Agent
  → deterministic Lead Ranking Engine
  → optional Reporter Agent
```

### Deterministic engine registry

Tools invoke engines; engines are not agents and do not create public routes. The registry is internal, typed, authorized, and audited.

| Engine | Computes | Typical tools |
|---|---|---|
| SQL Retrieval | filters, joins, counts, dates, totals | T01 |
| Search/Ranking | vector/BM25 retrieval, RRF, reranking | T02, T13 |
| Graph Intelligence | traversals, paths, communities, centrality | T03–T06 |
| Pattern Analysis | MO similarity, anomalies, clusters, temporal patterns | T08, T09 |
| Behavioral Profiling | deterministic profile features and review signals | T12 |
| Financial Analysis | transaction flows, layering, structuring, mule indicators | T11 |
| Forecasting | validated time-series projections and uncertainty | T10, T17 |
| Timeline | chronological reconstruction and gaps | T14 |
| Evidence/Explainability | citations, numbers, permissions, contradictions, confidence | T20, T22 |

### Evidence gate

The Evidence/Explainability Engine must validate every response before release: source coverage for factual claims, agreement of numbers with engine outputs, permission and investigation-scope filters, surfaced contradictions, explicit uncertainty, and audit metadata for the plan, sources, calculations, and model calls. Consequential conclusions remain subject to human review.

### Model router and resource budgets

LiteLLM selects Groq Llama 3.3 70B, Gemini 2.5 Flash, Mistral Small, or OpenRouter Llama 3.1 8B emergency fallback by task, complexity, quota, and fallback state. Business logic never hardcodes a provider. Resource controls are design targets pending measurement: avoid LLM calls for exact filters/counts/joins/paths/scores, precompute cards, bound graph depth and candidate sets, batch embeddings/writes, cache safe results, enforce token budgets and circuit breakers, and measure p50/p95/p99 latency, quality, citation coverage, unsupported-claim rate, and cost per investigation.

### Orchestrator detail

```python
class InvestigationOrchestrator:
    """LangGraph StateGraph; deterministic control plane, not an LLM agent."""
    # route, checkpoint, authorize, fan out engines, reconcile, retry, stream SSE
    ...
```

#### Planner Agent
```python
class PlannerAgent:
    """Optional intent-to-plan stage for ambiguous or complex requests."""
    ...
```

#### Reasoning Agent
```python
class ReasoningAgent:
    """Grounded synthesis and hypothesis evaluation over validated engine outputs."""
    ...
```

#### Reporter Agent
```python
class ReporterAgent:
    """Communication stage for cited summaries, timelines, bilingual text, and reports."""
    ...
```

## 2. The 23-Tool Registry

The registry remains the canonical internal T01–T23 contract. Each typed tool delegates to a deterministic engine or a reasoning stage as listed above; no tool is a public route and no engine is an agent.

Every capability the typed internal registry can invoke. Tools are typed, validated, and audited.

```python
from typing import TypedDict, Literal, Optional
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    """Base schema for all tool invocations."""
    tool_id: str          # T01-T23
    tool_name: str        # Human-readable name
    parameters: dict      # Tool-specific params
    timeout_ms: int = 30000
    retry_count: int = 2
    cache_key: Optional[str] = None  # For deduplication
```

### Data Retrieval Tools (T01–T03)

| ID | Tool | Backend | Latency | Description |
|----|------|---------|---------|-------------|
| **T01** | `sql_query` | Catalyst Data Store | Design target; measure | Structured filters on normalized Data Store |
| **T02** | `vector_search` | pgvector HNSW in Catalyst Data Store | Design target; measure | Semantic similarity search (cosine, 1024-dim BGE-M3) |
| **T03** | `graph_traverse` | Neo4j | Design target; measure | Cypher queries, N-hop relationship traversal |

```python
# T01: sql_query
class SQLQueryParams(BaseModel):
    table: Literal["firs", "accused", "victims", "arrests", "properties"]
    filters: dict[str, any]           # {"district": "Bengaluru Urban", "year": 2024}
    columns: list[str] = ["*"]
    limit: int = Field(default=100, le=1000)
    order_by: Optional[str] = None
    
# T02: vector_search  
class VectorSearchParams(BaseModel):
    query_text: str                    # Natural language query
    collection: Literal["fir_narratives", "mo_descriptions", "witness_statements"]
    top_k: int = Field(default=20, le=100)
    similarity_threshold: float = 0.7
    metadata_filter: Optional[dict] = None  # Pre-filter before vector search
    
# T03: graph_traverse
class GraphTraverseParams(BaseModel):
    start_entity: str                  # Entity ID or name
    entity_type: Literal["Person", "FIR", "Location", "Phone", "Vehicle", "Account"]
    relationship_types: list[str] = ["*"]  # ["ACCUSED_IN", "LINKED_TO", "TRANSACTED"]
    max_hops: int = Field(default=2, le=5)
    direction: Literal["outgoing", "incoming", "both"] = "both"
    return_paths: bool = True
```

### Graph Algorithm Tools (T04–T06)

| ID | Tool | Algorithm | Use Case |
|----|------|-----------|----------|
| **T04** | `community_detect` | Louvain / Label Prop | Find criminal gangs/networks |
| **T05** | `centrality_score` | PageRank / Betweenness | Identify kingpins, brokers |
| **T06** | `shortest_path` | Dijkstra / BFS | Entity-to-entity connection paths |

```python
# T04: community_detect
class CommunityDetectParams(BaseModel):
    subgraph_filter: Optional[str]     # Cypher WHERE clause for subgraph
    algorithm: Literal["louvain", "label_propagation", "wcc"] = "louvain"
    relationship_weight: Optional[str] = None  # Property to use as weight
    min_community_size: int = 3
    
# T05: centrality_score
class CentralityScoreParams(BaseModel):
    entity_type: str                   # Node label to score
    algorithm: Literal["pagerank", "betweenness", "degree", "closeness"] = "pagerank"
    subgraph_filter: Optional[str] = None
    top_k: int = 20
    damping_factor: float = 0.85       # PageRank damping
    
# T06: shortest_path
class ShortestPathParams(BaseModel):
    source_entity: str                 # Start node ID
    target_entity: str                 # End node ID
    relationship_types: list[str] = ["*"]
    max_depth: int = Field(default=6, le=10)
    algorithm: Literal["dijkstra", "bfs", "a_star"] = "dijkstra"
    weight_property: Optional[str] = None
```

### Intelligence Tools (T07–T10)

| ID | Tool | Method | Use Case |
|----|------|--------|----------|
| **T07** | `entity_resolve` | Fuzzy + Phonetic | Match aliases, spelling variants |
| **T08** | `pattern_match` | HDBSCAN + Vectors | MO clustering, serial crime detection |
| **T09** | `temporal_analysis` | Prophet + Stats | Time-series trends, anomaly detection |
| **T10** | `hotspot_detect` | H3 Hexagons | Spatial clustering of incidents |

```python
# T07: entity_resolve
class EntityResolveParams(BaseModel):
    name: str                          # Input name to resolve
    entity_type: Literal["person", "location", "phone", "vehicle"]
    methods: list[Literal["fuzzy", "phonetic", "alias_table", "ml_embedding"]] = ["fuzzy", "phonetic"]
    threshold: float = 0.80            # Match confidence threshold
    include_kannada: bool = True       # Cross-script matching
    
# T08: pattern_match
class PatternMatchParams(BaseModel):
    crime_category: Optional[str] = None
    time_window_days: int = 365
    min_cluster_size: int = 5
    features: list[Literal["mo_vector", "location", "time_of_day", "target_type"]]
    algorithm: Literal["hdbscan", "dbscan", "kmeans"] = "hdbscan"
    
# T09: temporal_analysis
class TemporalAnalysisParams(BaseModel):
    metric: str                        # What to analyze (e.g., "fir_count")
    group_by: Optional[str] = None     # District, crime type, etc.
    granularity: Literal["daily", "weekly", "monthly"] = "weekly"
    lookback_days: int = 730           # 2 years default
    forecast_days: int = 90
    detect_anomalies: bool = True
    
# T10: hotspot_detect
class HotspotDetectParams(BaseModel):
    crime_category: Optional[str] = None
    time_window_days: int = 90
    h3_resolution: int = Field(default=8, ge=6, le=10)  # 6=~36km², 8=~0.7km², 10=~0.015km²
    min_incidents: int = 5
    return_geojson: bool = True
```

### Domain-Specific Tools (T11–T14)

| ID | Tool | Domain | Use Case |
|----|------|--------|----------|
| **T11** | `financial_trail` | FinCrime | UPI/account graph traversal |
| **T12** | `offender_profile` | Behavioral | Pre-computed risk cards |
| **T13** | `similar_cases` | Case Matching | Vector + structural similarity |
| **T14** | `timeline_build` | Temporal | Chronological event assembly |

```python
# T11: financial_trail
class FinancialTrailParams(BaseModel):
    account_id: Optional[str] = None
    upi_id: Optional[str] = None
    phone_number: Optional[str] = None
    direction: Literal["incoming", "outgoing", "both"] = "both"
    max_hops: int = Field(default=4, le=8)
    min_amount: float = 0
    time_window_days: int = 90
    flag_mules: bool = True            # Highlight suspected mule accounts
    
# T12: offender_profile
class OffenderProfileParams(BaseModel):
    person_id: Optional[str] = None
    name: Optional[str] = None         # Falls back to entity_resolve
    include_sections: list[Literal[
        "risk_score", "criminal_history", "associates", 
        "mo_pattern", "escalation", "locations", "financial"
    ]] = ["risk_score", "criminal_history", "associates"]
    
# T13: similar_cases
class SimilarCasesParams(BaseModel):
    reference_fir_id: Optional[str] = None
    description: Optional[str] = None  # Free-text MO description
    similarity_method: Literal["vector", "structural", "hybrid"] = "hybrid"
    crime_category_filter: Optional[str] = None
    top_k: int = 10
    min_similarity: float = 0.70
    
# T14: timeline_build
class TimelineBuildParams(BaseModel):
    entity_id: str                     # Person, FIR, or Location ID
    entity_type: str
    time_range_days: int = 365
    include_events: list[Literal[
        "firs", "arrests", "court_dates", "bail", 
        "transactions", "sightings", "associates_activity"
    ]] = ["firs", "arrests", "court_dates"]
    format: Literal["json", "markdown", "vis_timeline"] = "json"
```

### Reasoning & Output Tools (T15–T18)

| ID | Tool | Purpose | Output |
|----|------|---------|--------|
| **T15** | `lead_generate` | Evidence gap reasoning | Ranked investigative leads |
| **T16** | `case_summarize` | Structured summary | Summary with citations |
| **T17** | `forecast_crime` | Predictive model | Prophet forecasts |
| **T18** | `demographic_correlate` | Social indicators | Correlation analysis |

```python
# T15: lead_generate
class LeadGenerateParams(BaseModel):
    evidence_collected: list[str]      # IDs of evidence gathered so far
    hypotheses: list[str]              # Current working hypotheses
    investigation_goal: str            # What we're trying to prove/disprove
    max_leads: int = 10
    include_rationale: bool = True
    
# T16: case_summarize
class CaseSummarizeParams(BaseModel):
    fir_ids: list[str]                 # Cases to summarize
    include_sections: list[Literal[
        "overview", "key_findings", "evidence", "timeline",
        "connections", "risk_assessment", "recommendations"
    ]] = ["overview", "key_findings", "evidence", "recommendations"]
    max_words: int = 500
    language: Literal["en", "kn"] = "en"
    cite_sources: bool = True
    
# T17: forecast_crime
class ForecastCrimeParams(BaseModel):
    district: Optional[str] = None     # None = state-wide
    crime_category: Optional[str] = None
    forecast_horizon_days: int = 90
    confidence_interval: float = 0.95
    include_components: bool = True    # Trend, seasonality, holidays
    
# T18: demographic_correlate
class DemographicCorrelateParams(BaseModel):
    crime_metric: str                  # "theft_rate", "cybercrime_count", etc.
    indicators: list[str]              # ["unemployment", "literacy", "urbanization"]
    geography_level: Literal["district", "subdivision", "station"] = "district"
    method: Literal["pearson", "spearman", "mutual_info"] = "spearman"
```

### System Tools (T19–T23)

| ID | Tool | Function | Integration |
|----|------|----------|-------------|
| **T19** | `translate` | EN↔KN translation | IndicTrans2 ONNX |
| **T20** | `explain_reasoning` | Reasoning trace | Structured explanation |
| **T21** | `generate_report` | PDF generation | WeasyPrint / SmartBrowz |
| **T22** | `pin_evidence` | Evidence board | Investigation state |
| **T23** | `alert_create` | Real-time alerts | Catalyst Signals |

```python
# T19: translate
class TranslateParams(BaseModel):
    text: str
    source_lang: Literal["en", "kn"] = "en"
    target_lang: Literal["en", "kn"] = "kn"
    model: str = "indictrans2-onnx"
    preserve_entities: bool = True     # Don't translate proper nouns
    
# T20: explain_reasoning
class ExplainReasoningParams(BaseModel):
    conclusion: str                    # The claim being explained
    evidence_chain: list[str]          # Ordered evidence IDs
    confidence: float                  # 0-1 confidence score
    alternative_explanations: list[str] = []
    format: Literal["structured", "narrative", "bullet"] = "structured"
    
# T21: generate_report
class GenerateReportParams(BaseModel):
    report_type: Literal["investigation", "intelligence", "briefing", "alert"]
    template: str = "default"
    sections: list[str]                # Content section IDs to include
    format: Literal["pdf", "html", "markdown"] = "pdf"
    language: Literal["en", "kn"] = "en"
    include_charts: bool = True
    classification: Literal["open", "restricted", "confidential"] = "restricted"
    
# T22: pin_evidence
class PinEvidenceParams(BaseModel):
    investigation_id: str              # Active investigation
    evidence_type: Literal["fir", "person", "connection", "pattern", "financial", "location"]
    evidence_id: str                   # Reference to the artifact
    note: Optional[str] = None         # Officer's annotation
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    
# T23: alert_create
class AlertCreateParams(BaseModel):
    alert_type: Literal["new_fir_match", "entity_activity", "pattern_trigger", "threshold_breach"]
    condition: dict                    # Trigger condition specification
    notify_channels: list[Literal["app", "sms", "email"]] = ["app"]
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    expires_days: int = 30
    investigation_id: Optional[str] = None
```

---

## 3. LangGraph Investigation Orchestrator

The Investigation Orchestrator is a LangGraph `StateGraph`, not an LLM agent. It routes fast/deep work, invokes typed registry tools, fans out independent deterministic engines, reconciles evidence, checkpoints case memory, retries bounded failures, and streams SSE progress.

### InvestigationState TypedDict

```python
class InvestigationState(TypedDict):
    query: str
    session_id: str
    officer_id: str
    authorization: dict
    route: Literal["fast", "deep"]
    execution_plan: dict | None
    engine_results: dict[str, list[dict]]
    evidence_board: list[dict]
    hypotheses: list[dict]
    structured_rationale: list[dict]
    citations: list[dict]
    contradictions: list[dict]
    confidence: float
    leads: list[dict]
    timeline: list[dict]
    package: dict | None
    errors: list[dict]
    tool_calls_made: list[dict]
    checkpoint_id: str | None
```

### Graph nodes and routing

```python
from langgraph.graph import StateGraph, END

builder = StateGraph(InvestigationState)
builder.add_node("route", route_request)                 # deterministic classification
builder.add_node("planner", optional_planner_stage)      # only ambiguous/complex input
builder.add_node("engines", invoke_typed_engines)        # SQL/search/graph/etc.
builder.add_node("evidence_gate", validate_evidence)     # mandatory release gate
builder.add_node("reasoner", grounded_reasoning_stage)  # deep path only
builder.add_node("lead_ranking", rank_leads)             # deterministic engine
builder.add_node("reporter", reporter_stage)             # wording/package only

builder.set_entry_point("route")
builder.add_conditional_edges("route", choose_fast_or_deep,
                              {"fast": "engines", "deep": "planner"})
builder.add_edge("planner", "engines")
builder.add_edge("engines", "evidence_gate")
builder.add_conditional_edges("evidence_gate", needs_reasoner,
                              {"reason": "reasoner", "rank": "lead_ranking"})
builder.add_edge("reasoner", "lead_ranking")
builder.add_conditional_edges("lead_ranking", needs_reporter,
                              {"report": "reporter", "done": END})
builder.add_edge("reporter", END)
```

Independent engine calls run in parallel only when the plan and resource budget permit it; actual concurrency and latency are measured acceptance criteria. Exact filters, counts, joins, paths, dates, and deterministic scores use the fast path without an LLM.

### Catalyst-compatible checkpoint adapter — persistent case memory

Investigation state survives across sessions through a Catalyst-compatible checkpoint adapter backed by Catalyst Data Store, with Catalyst Cache for hot session state. The adapter must be validated against deployed Catalyst APIs.

```python
class CatalystCheckpointAdapter:
    async def put(self, thread_id: str, state: dict) -> None: ...
    async def get(self, thread_id: str) -> dict | None: ...

checkpointer = CatalystCheckpointAdapter()
compiled_graph = builder.compile(checkpointer=checkpointer)
```

## 4. Engine-to-Tool Mapping

Tools are typed, authorized, audited registry entries. They invoke engines; engines are not agents. Planner, Reasoner, and Reporter are the only LLM-powered stages.

```python
ENGINE_TOOL_REGISTRY = {
    "sql_retrieval": ["T01_sql_query"],
    "search_ranking": ["T02_vector_search", "T13_similar_cases"],
    "graph_intelligence": ["T03_graph_traverse", "T04_community_detect", "T05_centrality_score", "T06_shortest_path"],
    "pattern_analysis": ["T08_pattern_match", "T09_temporal_analysis"],
    "forecasting": ["T10_hotspot_detect", "T17_forecast_crime"],
    "financial_analysis": ["T11_financial_trail"],
    "behavioral_profiling": ["T12_offender_profile"],
    "timeline": ["T14_timeline_build"],
    "lead_ranking": ["T15_lead_generate"],
    "communication": ["T16_case_summarize", "T19_translate", "T21_generate_report", "T23_alert_create"],
    "evidence_explainability": ["T20_explain_reasoning", "T22_pin_evidence"],
}
```

Authorization is applied before each tool call. The Evidence/Explainability Engine validates source coverage, numbers, citations, permissions, contradictions, and confidence before any response or package is released.

## 5. Execution Flow Example

### Query: “Find links between recent UPI fraud cases in Whitefield”

This is an illustrative trace; timings, counts, scores, and quality remain pending benchmark validation.

```text
Orchestrator: classify as complex relational query; create checkpoint
Planner:      produce validated plan referencing T01/T02/T03/T08/T11/T13/T14/T15/T20
Parallel engines:
  SQL Retrieval       → jurisdiction/date/category-filtered FIR records
  Search/Ranking      → semantic and lexical candidates, RRF/rerank
  Graph Intelligence  → bounded paths, communities, centrality
  Pattern Analysis    → MO and temporal clusters
  Financial Analysis  → account flows and transaction-derived indicators
  Behavioral Profiling→ profile features for authorized entities
Evidence gate:        reconcile sources, validate numbers/citations/RBAC, surface conflicts
Reasoner:             evaluate hypotheses using only validated structured results
Lead Ranking Engine:  deterministically rank evidence-backed next steps
Reporter (requested): produce cited summary, timeline, and package wording
```

The officer sees an evidence board, network graph, timeline, financial trail, ranked leads, similar-case references, uncertainty, and citations. Risk, ranking, and forecast outputs are review signals—not legal or factual determinations beyond their cited source basis.

## 6. Why This Beats 100+ Teams

### The Competition (What Others Build)

```
┌─────────────────────────────────────────────────────┐
│  TYPICAL HACKATHON SUBMISSION                        │
│                                                      │
│  User Question ──→ Single LLM Call ──→ Text Answer  │
│                                                      │
│  Problems:                                           │
│  • No tools — can't access real data                │
│  • No memory — forgets between messages             │
│  • No reasoning — single-shot generation            │
│  • No verification — hallucinations unchecked       │
│  • No artifacts — just text in a chat bubble        │
│  • No parallel execution — sequential only          │
│  • No domain knowledge — generic model              │
└─────────────────────────────────────────────────────┘
```

### What We Build: Orchestrator plus deterministic engines

```text
Officer query
   │
   ├─ Exact/structured ──► deterministic SQL/Search/Graph/Timeline engine
   │                       └─► Evidence gate ──► cited response (no LLM)
   │
   └─ Ambiguous/complex ─► optional Planner Agent
                           └─► parallel deterministic engines
                               └─► reconciliation + Evidence gate
                                   └─► Reasoning Agent
                                       └─► deterministic Lead Ranking Engine
                                           └─► optional Reporter Agent

Output package: evidence board • network graph • timeline • financial trail •
ranked leads • similar cases • cited summary • authorized report artifacts
```

The diagram shows control flow, not a promise of a fixed number of calls or a completed benchmark. Every engine result is typed, permission-checked, provenance-linked, and available for human review.

### Head-to-Head Comparison

| Dimension | Other Teams | KSP InvestigateAI |
|-----------|-------------|-------------------|
| **Architecture** | Single LLM chain | LangGraph orchestrator + Planner/Reasoning/Reporter stages + deterministic engines |
| **Data Access** | Maybe RAG (1 method) | 4-way hybrid retrieval + graph |
| **Tools** | 0-3 generic | 23 typed and engine-backed |
| **Parallelism** | Sequential only | Parallel deterministic-engine fan-out where permitted; benchmark pending |
| **Memory** | Session only (lost on refresh) | Catalyst-compatible checkpoint (retention subject to validation) |
| **Reasoning** | Single-shot generation | Grounded structured rationale + hypothesis testing |
| **Confidence** | None (or made up) | Calibrated 0-1 with evidence support |
| **Output** | Text in chat bubble | Multi-artifact investigation package |
| **Verification** | None | Citations, evidence chains, traces |
| **Domain** | Generic | KSP crime data, Karnataka geography, Kannada NLP |
| **Latency** | To be measured | Design target; benchmark before claiming |
| **Resumability** | Start over each time | Continue where you left off |

### The Multiplier Effect

```python
"""
Why typed tools backed by deterministic engines matter:

1. SPECIALIZATION: Each reasoning stage has a focused system prompt,
   optimized temperature, and restricted tool access.
   → Better results than one agent trying to do everything.

2. PARALLELISM: Independent engines may run simultaneously when the plan and budget permit.
   → Parallelism is a design strategy; throughput requires measurement.

3. COMPOSABILITY: Engines and reasoning stages can be recombined for new use cases
   without rewriting. Add a typed tool? The orchestrator can authorize it for the relevant engine/stage.
   → O(1) feature addition, not O(n).

4. AUDITABILITY: Every tool call is logged, every reasoning 
   step is traceable, every conclusion has citations.
   → Critical for law enforcement accountability.

5. RESILIENCE: One engine fails? Bounded retries and graceful degradation preserve available results.
   Graph DB down? SQL + vector still work.
   → Graceful degradation, not total failure.

6. MEMORY: Officer builds up investigation over days.
   Case memory accumulates evidence, refines hypotheses, and tracks progress.
   → Compound intelligence, not stateless Q&A.
"""
```

---

## Quick Start — Running the Investigation Orchestrator

```python
from src.orchestration.orchestrator import InvestigateAI
from src.orchestration.config import OrchestratorConfig

# Initialize the orchestrator
ai = InvestigateAI(config=OrchestratorConfig.from_env())
await ai.initialize()  # Connects to all backends

# Run an investigation
result = await ai.investigate(
    query="Find links between recent UPI fraud cases in Whitefield",
    officer_id="KSP_IO_4521",
    session_id="inv_2026_07_001"
)

# Access results
print(result.summary)           # Natural language summary
print(result.leads)             # Ranked investigative leads
print(result.confidence)        # 0.78
print(result.report_url)        # /reports/inv_2026_07_001.pdf
print(result.timeline)          # Chronological events
print(result.network_graph)     # Vis.js compatible graph data
```

---

*This document defines the core AI architecture. For implementation details, see:*
- `src/orchestration/` — Orchestration and reasoning-stage implementations
- `src/registry/` — Tool registry and implementations
- `src/graph/` — LangGraph state machine definition
- `.LOCK/DATA_ARCHITECTURE.md` — Data layer powering the tools
- `.LOCK/MASTER_PLAN.md` — Overall system design
