# 🤖 AI Agent Fleet Architecture — KSP InvestigateAI

> **Classification**: CORE DIFFERENTIATOR — Palantir Gotham-level multi-agent orchestration  
> **Version**: 1.0.0  
> **Last Updated**: 2026-07-23  
> **Entry Point**: `src/agents/orchestrator.py`

---

## Why Agents, Not a Chatbot

```
❌ Chatbot:    Question → LLM → Answer (single inference, no tools, no memory)
✅ This:       Question → PLAN → 5-7 PARALLEL TOOL CALLS → REASON → MULTI-ARTIFACT PACKAGE
```

KSP InvestigateAI deploys a **fleet of 10 specialized agents**, each with distinct capabilities, tool access, and reasoning strategies. They coordinate through a **LangGraph state machine** with persistent memory, parallel execution, and conditional routing.

---

## 1. Agent Fleet Overview

| # | Agent | Role | Model | Tools |
|---|-------|------|-------|-------|
| 1 | **Investigation Orchestrator** | LangGraph state machine — routes, checkpoints, manages lifecycle | — (graph engine) | All (dispatch) |
| 2 | **Planner Agent** | Decomposes NL query → structured execution plan | GPT-4o / Claude 3.5 | T01, T07, T19 |
| 3 | **Evidence Collector Agent** | 4-way hybrid retrieval (SQL + vector + graph + full-text) | GPT-4o-mini | T01, T02, T03, T07 |
| 4 | **Graph Analyzer Agent** | Neo4j Cypher + GDS algorithms (communities, centrality) | GPT-4o | T03, T04, T05, T06 |
| 5 | **Pattern Detector Agent** | Clustering, time-series anomalies, MO matching | GPT-4o | T08, T09, T10, T17 |
| 6 | **Behavioral Profiler Agent** | Risk scoring, escalation detection, offender cards | GPT-4o-mini | T12, T09, T18 |
| 7 | **Financial Analyst Agent** | UPI/account graphs, money trails, mule detection | GPT-4o | T11, T03, T05, T06 |
| 8 | **Reasoner Agent** | Chain-of-Thought + hypothesis evaluation + confidence | Claude 3.5 Sonnet | T15, T20, T13 |
| 9 | **Decision Support Agent** | Leads, similar cases, actionable recommendations | GPT-4o | T13, T15, T16, T22 |
| 10 | **Reporter Agent** | Investigation packages — PDF, timeline, summary | GPT-4o-mini | T16, T14, T21, T23 |

### Agent Detail Cards

#### 1. Investigation Orchestrator
```python
"""
The Orchestrator is NOT an LLM agent — it's the LangGraph StateGraph itself.
It manages:
  - State transitions between agents
  - Conditional routing (simple → fast path, complex → full pipeline)
  - Parallel fan-out/fan-in execution
  - PostgreSQL checkpointing for persistent memory
  - Error recovery and retry logic
"""
```

#### 2. Planner Agent
```python
class PlannerAgent:
    """
    Decomposes natural language into a structured execution plan.
    
    Input:  "Find links between recent UPI fraud cases in Whitefield"
    Output: ExecutionPlan(
        intent="relationship_discovery",
        complexity="complex",
        entities=["UPI fraud", "Whitefield"],
        temporal_filter=TimeRange(days=90),
        required_tools=[T01, T02, T03, T11, T05],
        parallel_groups=[
            ["evidence_collector"],
            ["graph_analyzer", "pattern_detector", "financial_analyst"],
            ["reasoner"],
            ["decision_support", "reporter"]
        ]
    )
    """
    model: str = "gpt-4o"
    temperature: float = 0.1  # Low creativity, high precision
    system_prompt: str = PLANNER_SYSTEM_PROMPT
    max_tools_per_plan: int = 12
    
    def decompose(self, query: str, context: InvestigationState) -> ExecutionPlan:
        ...
```

#### 3. Evidence Collector Agent
```python
class EvidenceCollectorAgent:
    """
    4-Way Hybrid Retrieval Strategy:
      1. SQL (structured filters — date, station, crime type)
      2. Vector (semantic similarity — pgvector cosine)
      3. Graph (relationship traversal — Neo4j 1-3 hops)
      4. Full-text (keyword search — PostgreSQL tsvector)
    
    Results are fused using Reciprocal Rank Fusion (RRF):
      score = Σ 1/(k + rank_i) for each retrieval method
    """
    retrieval_methods: list = ["sql", "vector", "graph", "fulltext"]
    fusion_k: int = 60  # RRF constant
    max_results_per_method: int = 50
    final_top_k: int = 20
```

#### 4. Graph Analyzer Agent
```python
class GraphAnalyzerAgent:
    """
    Executes Neo4j Cypher queries and GDS algorithms:
      - Community detection (Louvain, Label Propagation)
      - Centrality (PageRank, Betweenness, Degree)
      - Pathfinding (Dijkstra, A*, all shortest paths)
      - Similarity (Node Similarity, Jaccard)
    
    Translates LLM-generated intent into optimized Cypher.
    """
    neo4j_driver: AsyncDriver
    gds_client: GraphDataScience
    max_hops: int = 5
    timeout_ms: int = 30000
```

#### 5. Pattern Detector Agent
```python
class PatternDetectorAgent:
    """
    Detects criminal patterns across multiple dimensions:
      - MO Clustering: HDBSCAN on crime description embeddings
      - Temporal Anomalies: Prophet forecast + residual spikes
      - Spatial Hotspots: H3 hexagon density clustering
      - Escalation Patterns: time-series of severity scores
    """
    clustering_algorithm: str = "hdbscan"
    min_cluster_size: int = 5
    prophet_changepoint_prior: float = 0.05
    h3_resolution: int = 8  # ~460m hexagons
```

#### 6. Behavioral Profiler Agent
```python
class BehavioralProfilerAgent:
    """
    Builds and scores offender behavioral profiles:
      - Risk Score: 0-100 composite (recency, frequency, severity, escalation)
      - Escalation Detection: increasing severity over time windows
      - Demographic Correlation: social indicators overlay
      - Network Position: centrality in criminal graph
    """
    risk_weights: dict = {
        "recency": 0.25,
        "frequency": 0.30,
        "severity": 0.25,
        "escalation": 0.20
    }
    escalation_window_days: int = 180
```

#### 7. Financial Analyst Agent
```python
class FinancialAnalystAgent:
    """
    Traces money flows through UPI/banking networks:
      - Account Graph Traversal: follow the money N hops
      - Mule Detection: accounts with high fan-in/fan-out ratios
      - Layering Detection: rapid pass-through transactions
      - Amount Pattern Analysis: structuring below thresholds
    """
    max_traversal_depth: int = 6
    mule_fanout_threshold: int = 10
    structuring_threshold_inr: int = 49000  # Just below 50K reporting
```

#### 8. Reasoner Agent
```python
class ReasonerAgent:
    """
    The 'thinking' agent — synthesizes evidence into conclusions:
      - Chain-of-Thought: structured multi-step reasoning
      - Hypothesis Generation: propose explanations for evidence
      - Hypothesis Evaluation: score each against evidence (support/contradict/neutral)
      - Confidence Scoring: calibrated 0-1 confidence with uncertainty bounds
      - Citation Tracking: every claim linked to source evidence
    """
    model: str = "claude-3-5-sonnet"  # Best at reasoning
    temperature: float = 0.3
    max_hypotheses: int = 5
    min_confidence_to_present: float = 0.4
```

#### 9. Decision Support Agent
```python
class DecisionSupportAgent:
    """
    Transforms analysis into actionable intelligence:
      - Lead Generation: ranked next-steps with expected value
      - Similar Cases: vector + structural case matching
      - Recommendations: prioritized actions for the officer
      - Evidence Gaps: what's missing and how to get it
    """
    max_leads: int = 10
    similarity_threshold: float = 0.75
    recommendation_categories: list = ["immediate", "investigate", "monitor", "archive"]
```

#### 10. Reporter Agent
```python
class ReporterAgent:
    """
    Generates investigation packages:
      - PDF Report: WeasyPrint formatted with KSP branding
      - Timeline: chronological event visualization data
      - Summary: structured case summary with key findings
      - Evidence Board: pinned artifacts for case file
      - Alerts: real-time signals for ongoing monitoring
    """
    pdf_engine: str = "weasyprint"  # SmartBrowz for complex layouts
    template_dir: str = "templates/reports/"
    max_summary_words: int = 500
```

---

## 2. The 23-Tool Registry

Every capability the AI fleet can invoke. Tools are typed, validated, and audited.

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
| **T01** | `sql_query` | PostgreSQL | <100ms | Structured filters on normalized Data Store |
| **T02** | `vector_search` | pgvector | <200ms | Semantic similarity search (cosine, 768-dim) |
| **T03** | `graph_traverse` | Neo4j | <500ms | Cypher queries, N-hop relationship traversal |

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

## 3. LangGraph State Machine — Full Graph Definition

The Investigation Orchestrator is implemented as a **LangGraph StateGraph** — not a simple chain, but a full directed graph with conditional routing, parallel execution, and persistent checkpointing.

### InvestigationState TypedDict

```python
from typing import TypedDict, Optional, Annotated
from langgraph.graph import add_messages
from datetime import datetime
from enum import Enum

class Complexity(Enum):
    SIMPLE = "simple"          # Direct lookup, 1-2 tools
    MODERATE = "moderate"      # Multi-step, 3-4 tools
    COMPLEX = "complex"        # Full pipeline, 5+ tools, parallel
    CRITICAL = "critical"      # High-stakes, requires human review

class InvestigationState(TypedDict):
    """Complete state flowing through the agent graph."""
    
    # === Input ===
    query: str                                    # Original officer query (EN or KN)
    query_english: str                            # Translated to English if needed
    session_id: str                               # Persistent session identifier
    officer_id: str                               # Authenticated officer
    officer_rank: str                             # For access control
    timestamp: datetime                           # Query timestamp
    
    # === Planning ===
    intent: str                                   # Classified intent
    complexity: Complexity                        # Routing decision
    execution_plan: dict                          # Structured plan from Planner
    entities_extracted: list[dict]                # NER results
    temporal_filter: Optional[dict]               # Time range if specified
    spatial_filter: Optional[dict]                # Location if specified
    
    # === Evidence Collection ===
    sql_results: list[dict]                       # From T01
    vector_results: list[dict]                    # From T02 (with scores)
    graph_results: list[dict]                     # From T03
    fulltext_results: list[dict]                  # Full-text search hits
    fused_evidence: list[dict]                    # RRF-merged ranked list
    evidence_count: int                           # Total evidence pieces
    
    # === Analysis ===
    communities: list[dict]                       # From T04 (gang clusters)
    centrality_scores: list[dict]                 # From T05 (key players)
    paths: list[dict]                             # From T06 (connections)
    patterns: list[dict]                          # From T08 (MO clusters)
    temporal_analysis: Optional[dict]             # From T09 (trends)
    hotspots: list[dict]                          # From T10 (spatial)
    financial_trails: list[dict]                  # From T11 (money flow)
    behavioral_profiles: list[dict]              # From T12 (risk cards)
    
    # === Reasoning ===
    hypotheses: list[dict]                        # Generated hypotheses
    hypothesis_scores: list[dict]                 # Evidence support scores
    confidence: float                             # Overall confidence 0-1
    reasoning_trace: list[dict]                   # Step-by-step CoT
    citations: list[dict]                         # Evidence → claim mapping
    
    # === Output ===
    leads: list[dict]                             # Ranked next steps
    similar_cases: list[dict]                     # Matching past cases
    recommendations: list[dict]                   # Actionable items
    summary: str                                  # Natural language summary
    timeline: list[dict]                          # Chronological events
    report_url: Optional[str]                     # Generated PDF URL
    alerts_created: list[str]                     # Alert IDs created
    
    # === Meta ===
    messages: Annotated[list, add_messages]       # Chat history
    errors: list[dict]                            # Error log
    tool_calls_made: list[dict]                   # Audit trail
    execution_time_ms: int                        # Total elapsed
    tokens_used: int                              # LLM token count
    checkpoint_id: Optional[str]                  # For resumption
```

### Node Definitions

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Initialize the graph
graph = StateGraph(InvestigationState)

# === Add Nodes (each agent is a node) ===
graph.add_node("planner", planner_agent.invoke)
graph.add_node("evidence_collector", evidence_collector_agent.invoke)
graph.add_node("graph_analyzer", graph_analyzer_agent.invoke)
graph.add_node("pattern_detector", pattern_detector_agent.invoke)
graph.add_node("behavioral_profiler", behavioral_profiler_agent.invoke)
graph.add_node("financial_analyst", financial_analyst_agent.invoke)
graph.add_node("reasoner", reasoner_agent.invoke)
graph.add_node("decision_support", decision_support_agent.invoke)
graph.add_node("reporter", reporter_agent.invoke)

# === Parallel Analysis Hub (fan-out / fan-in) ===
from langgraph.graph import Send

def route_to_analyzers(state: InvestigationState) -> list[Send]:
    """Fan-out: send state to multiple analyzers in parallel."""
    plan = state["execution_plan"]
    sends = []
    
    if "graph_analysis" in plan["required_capabilities"]:
        sends.append(Send("graph_analyzer", state))
    if "pattern_detection" in plan["required_capabilities"]:
        sends.append(Send("pattern_detector", state))
    if "behavioral_profiling" in plan["required_capabilities"]:
        sends.append(Send("behavioral_profiler", state))
    if "financial_analysis" in plan["required_capabilities"]:
        sends.append(Send("financial_analyst", state))
    
    # At minimum, always run graph analyzer
    if not sends:
        sends.append(Send("graph_analyzer", state))
    
    return sends
```

### Edge Definitions — Conditional Routing

```python
def route_by_complexity(state: InvestigationState) -> str:
    """Route based on query complexity determined by Planner."""
    complexity = state["complexity"]
    
    if complexity == Complexity.SIMPLE:
        # Fast path: skip analysis, go straight to decision support
        return "decision_support"
    elif complexity == Complexity.CRITICAL:
        # Full pipeline with all analyzers
        return "evidence_collector"
    else:
        # Standard path
        return "evidence_collector"

def should_generate_report(state: InvestigationState) -> str:
    """Decide if a full report is needed."""
    if state["complexity"] in [Complexity.COMPLEX, Complexity.CRITICAL]:
        return "reporter"
    if state.get("execution_plan", {}).get("generate_report", False):
        return "reporter"
    return END

# === Wire the Graph ===
# Entry point
graph.set_entry_point("planner")

# Planner → routes by complexity
graph.add_conditional_edges(
    "planner",
    route_by_complexity,
    {
        "evidence_collector": "evidence_collector",
        "decision_support": "decision_support",  # Simple fast-path
    }
)

# Evidence Collector → Parallel Analyzers (fan-out)
graph.add_conditional_edges(
    "evidence_collector",
    route_to_analyzers  # Returns list[Send] for parallel execution
)

# All Analyzers → Reasoner (fan-in / join)
graph.add_edge("graph_analyzer", "reasoner")
graph.add_edge("pattern_detector", "reasoner")
graph.add_edge("behavioral_profiler", "reasoner")
graph.add_edge("financial_analyst", "reasoner")

# Reasoner → Decision Support
graph.add_edge("reasoner", "decision_support")

# Decision Support → Reporter or END
graph.add_conditional_edges(
    "decision_support",
    should_generate_report,
    {
        "reporter": "reporter",
        END: END,
    }
)

# Reporter → END
graph.add_edge("reporter", END)
```

### Execution Graph Visualization

```
                    ┌─────────────┐
                    │   PLANNER   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │ SIMPLE     │ COMPLEX    │
              ▼            ▼            │
    ┌─────────────┐  ┌──────────────┐  │
    │  DECISION   │  │  EVIDENCE    │  │
    │  SUPPORT    │  │  COLLECTOR   │  │
    └──────┬──────┘  └──────┬───────┘  │
           │                │          │
           ▼         ┌──────┼──────────┼──────┐  ← PARALLEL FAN-OUT
          END        │      │          │      │
                     ▼      ▼          ▼      ▼
                ┌────────┐┌────────┐┌──────┐┌──────────┐
                │ GRAPH  ││PATTERN ││BEHAV ││FINANCIAL │
                │ANALYZER││DETECTOR││PROFIL││ ANALYST  │
                └───┬────┘└───┬────┘└──┬───┘└────┬─────┘
                    │         │        │         │
                    └─────────┴────┬───┴─────────┘  ← FAN-IN (JOIN)
                                   │
                              ┌────▼─────┐
                              │ REASONER │
                              └────┬─────┘
                                   │
                          ┌────────▼────────┐
                          │DECISION SUPPORT │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │ NO REPORT    │ REPORT       │
                    ▼              ▼              │
                   END       ┌──────────┐        │
                             │ REPORTER │        │
                             └────┬─────┘        │
                                  │              │
                                  ▼              │
                                 END             │
```

### PostgreSQL Checkpointer — Persistent Case Memory

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Initialize persistent checkpointer
DB_URI = "postgresql+asyncpg://ksp_agents:***@localhost:5432/ksp_investigations"

async def create_checkpointer():
    """Create PostgreSQL-backed checkpointer for persistent state."""
    checkpointer = AsyncPostgresSaver.from_conn_string(DB_URI)
    await checkpointer.setup()  # Creates checkpoint tables
    return checkpointer

# Compile graph with checkpointer
checkpointer = await create_checkpointer()
compiled_graph = graph.compile(checkpointer=checkpointer)

# === Invoke with thread_id for session persistence ===
config = {
    "configurable": {
        "thread_id": f"investigation_{officer_id}_{case_id}",  # Persistent key
    }
}

# First query at 10:00 AM
result = await compiled_graph.ainvoke(
    {"query": "Show me UPI fraud cases in Whitefield last 3 months"},
    config=config
)

# Officer returns NEXT DAY — state is fully preserved
# Same thread_id = same investigation context
result = await compiled_graph.ainvoke(
    {"query": "Now find connections between the top 3 accused"},
    config=config  # Same thread_id — AI REMEMBERS everything
)
```

#### How the Officer Returns Next Day and AI Remembers

```python
"""
SESSION PERSISTENCE ARCHITECTURE:

1. Every state transition is checkpointed to PostgreSQL
2. thread_id = f"investigation_{officer_id}_{case_id}"
3. When officer logs back in:
   a. Frontend sends same thread_id
   b. LangGraph loads last checkpoint from PostgreSQL
   c. Full InvestigationState is restored:
      - All evidence collected
      - All analysis performed
      - All hypotheses generated
      - Chat history
      - Pinned evidence
   d. Officer continues EXACTLY where they left off

4. Checkpoint cleanup:
   - Active investigations: kept indefinitely
   - Closed cases: archived after 90 days
   - Session without activity: pruned after 30 days

5. Multi-device: Officer starts on desktop, continues on mobile
   — same thread_id, same state, seamless.
"""

class InvestigationSession:
    """Manages persistent investigation sessions."""
    
    async def resume_or_create(
        self, officer_id: str, case_id: Optional[str] = None
    ) -> tuple[CompiledGraph, dict]:
        """Resume existing investigation or start new one."""
        thread_id = f"investigation_{officer_id}_{case_id or 'general'}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Check if checkpoint exists
        checkpoint = await self.checkpointer.aget(config)
        
        if checkpoint:
            # RESUME: Officer is back, full context preserved
            logger.info(f"Resuming investigation {thread_id}, "
                       f"last active: {checkpoint.metadata['timestamp']}")
            return self.compiled_graph, config
        else:
            # NEW: Fresh investigation
            logger.info(f"Starting new investigation {thread_id}")
            return self.compiled_graph, config
```

---

## 4. Agent-to-Tool Mapping

Which agent can invoke which tools. Enforced at runtime — agents cannot call tools outside their scope.

```python
AGENT_TOOL_PERMISSIONS: dict[str, list[str]] = {
    "planner": [
        "T01_sql_query",         # Quick lookups to understand data shape
        "T07_entity_resolve",    # Resolve ambiguous entity references
        "T19_translate",         # Translate Kannada queries to English
    ],
    "evidence_collector": [
        "T01_sql_query",         # Structured data retrieval
        "T02_vector_search",     # Semantic similarity search
        "T03_graph_traverse",    # Relationship traversal
        "T07_entity_resolve",    # Entity disambiguation
    ],
    "graph_analyzer": [
        "T03_graph_traverse",    # Deep graph exploration
        "T04_community_detect",  # Gang/network discovery
        "T05_centrality_score",  # Key player identification
        "T06_shortest_path",     # Connection discovery
    ],
    "pattern_detector": [
        "T08_pattern_match",     # MO clustering
        "T09_temporal_analysis", # Time-series anomalies
        "T10_hotspot_detect",    # Spatial clustering
        "T17_forecast_crime",    # Predictive forecasting
    ],
    "behavioral_profiler": [
        "T12_offender_profile",  # Pre-computed behavioral cards
        "T09_temporal_analysis", # Escalation time-series
        "T18_demographic_correlate",  # Social indicators
    ],
    "financial_analyst": [
        "T11_financial_trail",   # UPI/account graph traversal
        "T03_graph_traverse",    # Transaction network exploration
        "T05_centrality_score",  # Money hub detection
        "T06_shortest_path",     # Money flow paths
    ],
    "reasoner": [
        "T15_lead_generate",     # Evidence gap reasoning
        "T20_explain_reasoning", # Structured reasoning trace
        "T13_similar_cases",     # Case matching for validation
    ],
    "decision_support": [
        "T13_similar_cases",     # Similar case recommendations
        "T15_lead_generate",     # Investigative lead generation
        "T16_case_summarize",    # Structured summaries
        "T22_pin_evidence",      # Save to investigation board
    ],
    "reporter": [
        "T16_case_summarize",    # Summary generation
        "T14_timeline_build",    # Chronological assembly
        "T21_generate_report",   # PDF/HTML report generation
        "T23_alert_create",      # Real-time monitoring alerts
    ],
}
```

### Tool Access Matrix (Visual)

```
                    T01 T02 T03 T04 T05 T06 T07 T08 T09 T10 T11 T12 T13 T14 T15 T16 T17 T18 T19 T20 T21 T22 T23
Planner              ✓                           ✓                                               ✓
Evidence Collector   ✓   ✓   ✓                   ✓
Graph Analyzer               ✓   ✓   ✓   ✓
Pattern Detector                                         ✓   ✓   ✓                       ✓
Behav. Profiler                                              ✓            ✓                   ✓
Financial Analyst            ✓       ✓   ✓                           ✓
Reasoner                                                                  ✓       ✓            ✓
Decision Support                                                          ✓       ✓   ✓            ✓
Reporter                                                                       ✓       ✓            ✓   ✓
```

---

## 5. Execution Flow Example

### Query: "Find links between recent UPI fraud cases in Whitefield"

Full trace through the agent fleet:

```
TIME     AGENT               ACTION                                          TOOLS CALLED
─────────────────────────────────────────────────────────────────────────────────────────────
0ms      Orchestrator        Receives query, creates InvestigationState       —
15ms     Planner             Decompose NL → ExecutionPlan                     T07 (entity_resolve)
                             → Intent: relationship_discovery
                             → Complexity: COMPLEX
                             → Entities: ["UPI fraud", "Whitefield"]
                             → Temporal: last 90 days
                             → Route: FULL PIPELINE

180ms    Evidence Collector  4-way hybrid retrieval                           T01, T02, T03, T07
                             → T01: SELECT * FROM firs WHERE category='UPI Fraud' 
                                    AND station LIKE '%Whitefield%' AND date > now()-90d
                             → T02: vector_search("UPI fraud Whitefield", top_k=20)
                             → T03: MATCH (f:FIR)-[:ACCUSED_IN]-(p:Person)
                                    WHERE f.category='Cyber Crime' AND f.station='Whitefield'
                             → T07: Resolve "Whitefield" → ["Whitefield", "ITPL", "Kadugodi"]
                             → RRF Fusion: 34 unique evidence pieces, ranked

850ms    ┌─ Graph Analyzer   Community detection on accused network           T03, T04, T05, T06
         │                   → T04: Louvain → 3 communities (possible gangs)
         │                   → T05: PageRank → Top 5 central accused
         │                   → T06: Shortest path between top accused → 2-hop connection
         │                   
850ms    ├─ Pattern Detector MO clustering on fraud descriptions              T08, T09
         │                   → T08: HDBSCAN → 2 distinct MO clusters:
         │                      Cluster A: "OTP phishing via fake bank calls"
         │                      Cluster B: "QR code swap at merchant locations"
         │                   → T09: Temporal spike in Cluster B (last 3 weeks)
         │                   
850ms    ├─ Behav. Profiler  Risk scoring for identified accused              T12
         │                   → T12: 5 offender profiles retrieved
         │                      Accused #1: Risk 87/100 (repeat offender, escalating)
         │                      Accused #3: Risk 72/100 (new, rapid activity)
         │                   
850ms    └─ Financial Analyst UPI money trail analysis                        T11, T05
                             → T11: Trace from victim accounts → 3-hop → convergence 
                                    at 2 accounts (suspected mules)
                             → T05: Betweenness centrality → 1 account appears in 
                                    7/12 fraud trails (money hub)

2100ms   Reasoner            Synthesize all evidence                          T15, T20
                             → Chain-of-Thought reasoning:
                               1. 3 Louvain communities suggest organized operation
                               2. 2 MO clusters = 2 fraud teams or 1 team, 2 methods
                               3. Financial convergence at 2 mule accounts
                               4. PageRank leader (Accused #1) linked to both communities
                               5. Temporal spike correlates with Accused #3's first appearance
                             → Hypothesis: "Organized ring led by Accused #1, recently 
                                expanded by recruiting Accused #3 for QR code method"
                             → Confidence: 0.78
                             → T15: Generate leads:
                                Lead 1: "Investigate mule account holders (2 accounts)"
                                Lead 2: "Check Accused #1 ↔ #3 phone/location overlap"
                                Lead 3: "CCTV at QR-swap merchant locations"

2800ms   Decision Support    Package actionable intelligence                  T13, T16, T22
                             → T13: 2 similar case clusters found (2023 Koramangala ring)
                             → T16: Structured summary with 12 citations
                             → T22: Pin top 5 evidence pieces to investigation board
                             → Recommendations:
                               [IMMEDIATE] Freeze 2 mule accounts (RBI circular ref)
                               [INVESTIGATE] Accused #3 associates
                               [MONITOR] Create alert for new QR-swap reports

3200ms   Reporter            Generate investigation package                   T14, T21, T23
                             → T14: Timeline of 34 events across 90 days
                             → T21: PDF report (12 pages, charts, network graph)
                             → T23: Alert created: "New QR-swap fraud in Whitefield area"
                             
3500ms   Orchestrator        Return final InvestigationState to frontend      —
```

### What the Officer Sees (3.5 seconds later):

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Investigation Results                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Summary: Found organized UPI fraud ring operating in         │
│ Whitefield area with 2 distinct methods (OTP phishing +      │
│ QR swap). 3 connected communities, 12 cases linked.          │
│ Confidence: 78%                                              │
│                                                              │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│ │ 🕸️ Network  │  │ 📊 Timeline │  │ 💰 Money    │          │
│ │    Graph    │  │             │  │    Trail    │          │
│ └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
│ 🎯 Top Leads:                                               │
│ 1. Freeze mule accounts: XXXX7834, XXXX2901                 │
│ 2. Investigate Accused #1 ↔ #3 connection                    │
│ 3. CCTV review at 3 merchant locations                       │
│                                                              │
│ 📋 Similar Past Case: Koramangala Ring (2023) — convicted   │
│                                                              │
│ [📥 Download PDF] [🔔 Alert Active] [📌 5 items pinned]     │
└─────────────────────────────────────────────────────────────┘
```

---

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

### What We Build (Palantir Gotham-Level)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  KSP INVESTIGATEAI — MULTI-AGENT ORCHESTRATION                           │
│                                                                           │
│  Officer Question                                                         │
│       │                                                                   │
│       ▼                                                                   │
│  ┌─────────┐    Intent + Entities + Complexity                           │
│  │ PLANNER │───────────────────────────────────┐                         │
│  └─────────┘                                    │                         │
│       │                                         ▼                         │
│       ▼                                  ┌─────────────┐                 │
│  ┌───────────┐   34 evidence pieces      │ ROUTE BY    │                 │
│  │ COLLECTOR │◄──────────────────────────│ COMPLEXITY  │                 │
│  └───────────┘                           └─────────────┘                 │
│       │                                                                   │
│       ▼ PARALLEL (5-7 tool calls simultaneously)                         │
│  ┌─────────┬──────────┬─────────┬────────────┐                          │
│  │ GRAPH   │ PATTERN  │ BEHAV.  │ FINANCIAL  │                           │
│  │ANALYZER │ DETECTOR │ PROFILER│  ANALYST   │                           │
│  └────┬────┴────┬─────┴────┬────┴─────┬──────┘                          │
│       │         │          │          │                                   │
│       └─────────┴────┬─────┴──────────┘                                  │
│                      ▼                                                    │
│              ┌────────────┐   Hypotheses + Confidence                    │
│              │  REASONER  │   Chain-of-Thought + Citations               │
│              └─────┬──────┘                                              │
│                    ▼                                                      │
│          ┌──────────────────┐   Leads + Recommendations                  │
│          │ DECISION SUPPORT │   Similar Cases + Evidence Board            │
│          └────────┬─────────┘                                            │
│                   ▼                                                       │
│            ┌────────────┐   PDF + Timeline + Alerts                      │
│            │  REPORTER  │   Full Investigation Package                    │
│            └─────┬──────┘                                                │
│                  ▼                                                        │
│  ┌───────────────────────────────────────────────────────────────┐       │
│  │ MULTI-ARTIFACT OUTPUT:                                         │       │
│  │  • Network graph visualization                                 │       │
│  │  • Money trail diagram                                         │       │
│  │  • Chronological timeline                                      │       │
│  │  • Ranked leads with rationale                                 │       │
│  │  • Similar case references                                     │       │
│  │  • Downloadable PDF report                                     │       │
│  │  • Active monitoring alerts                                    │       │
│  │  • Pinned evidence board                                       │       │
│  │  • Confidence score with reasoning trace                       │       │
│  └───────────────────────────────────────────────────────────────┘       │
│                                                                           │
│  Total time: 3.5 seconds | Tools called: 14 | Parallel streams: 4       │
└──────────────────────────────────────────────────────────────────────────┘
```

### Head-to-Head Comparison

| Dimension | Other Teams | KSP InvestigateAI |
|-----------|-------------|-------------------|
| **Architecture** | Single LLM chain | 10-agent StateGraph |
| **Data Access** | Maybe RAG (1 method) | 4-way hybrid retrieval + graph |
| **Tools** | 0-3 generic | 23 specialized, typed |
| **Parallelism** | Sequential only | 4-way parallel fan-out |
| **Memory** | Session only (lost on refresh) | PostgreSQL checkpoint (days/weeks) |
| **Reasoning** | Single-shot generation | Multi-step CoT + hypothesis testing |
| **Confidence** | None (or made up) | Calibrated 0-1 with evidence support |
| **Output** | Text in chat bubble | Multi-artifact investigation package |
| **Verification** | None | Citations, evidence chains, traces |
| **Domain** | Generic | KSP crime data, Karnataka geography, Kannada NLP |
| **Latency** | 2-5s for text | 3.5s for full package (parallel) |
| **Resumability** | Start over each time | Continue where you left off |

### The Multiplier Effect

```python
"""
Why 10 agents × 23 tools ≠ just 'more code':

1. SPECIALIZATION: Each agent has a focused system prompt, 
   optimized temperature, and restricted tool access.
   → Better results than one agent trying to do everything.

2. PARALLELISM: 4 analyzers run simultaneously.
   → 4x throughput without sacrificing depth.

3. COMPOSABILITY: Agents can be recombined for new use cases
   without rewriting. Add a new tool? One agent gets it.
   → O(1) feature addition, not O(n).

4. AUDITABILITY: Every tool call is logged, every reasoning 
   step is traceable, every conclusion has citations.
   → Critical for law enforcement accountability.

5. RESILIENCE: One agent fails? Others still produce results.
   Graph DB down? SQL + vector still work.
   → Graceful degradation, not total failure.

6. MEMORY: Officer builds up investigation over days.
   AI accumulates evidence, refines hypotheses, tracks progress.
   → Compound intelligence, not stateless Q&A.
"""
```

---

## Quick Start — Running the Agent Fleet

```python
from src.agents.orchestrator import InvestigateAI
from src.agents.config import AgentConfig

# Initialize the fleet
ai = InvestigateAI(config=AgentConfig.from_env())
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
- `src/agents/` — Agent implementations
- `src/tools/` — Tool registry and implementations  
- `src/graph/` — LangGraph state machine definition
- `.LOCK/DATA_ARCHITECTURE.md` — Data layer powering the tools
- `.LOCK/MASTER_PLAN.md` — Overall system design
