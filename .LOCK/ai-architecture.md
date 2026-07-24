# AI System Architecture

> KSP InvestigateAI — Intelligence Layer Design Document
> Last Updated: 2026-07-23

---

## LLM Integration Layer

### Router Configuration (LiteLLM)

```yaml
model_list:
  - model_name: "investigateai-primary"
    litellm_params:
      model: groq/llama-3.1-70b-versatile
      api_key: os.environ/GROQ_API_KEY
      rpm: 30
      tpm: 100000
    priority: 1

  - model_name: "investigateai-fallback-1"
    litellm_params:
      model: gemini/gemini-1.5-pro
      api_key: os.environ/GEMINI_API_KEY
      rpm: 15
      tpm: 1000000
    priority: 2

  - model_name: "investigateai-fallback-2"
    litellm_params:
      model: mistral/mistral-large-latest
      api_key: os.environ/MISTRAL_API_KEY
      rpm: 10
      tpm: 500000
    priority: 3

  - model_name: "investigateai-fallback-3"
    litellm_params:
      model: openrouter/meta-llama/llama-3.1-70b-instruct
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 10
      tpm: 200000
    priority: 4

router_settings:
  routing_strategy: "priority-based"
  fallbacks:
    - investigateai-primary: [investigateai-fallback-1, investigateai-fallback-2, investigateai-fallback-3]
  retry_policy:
    max_retries: 3
    retry_after: 5
```

**Routing Logic:** Groq primary (lowest latency) → Gemini fallback (largest context) → Mistral (EU compliance) → OpenRouter (last resort aggregator)

### Structured Output

Every agent output is validated through Pydantic models:

```python
class AgentOutput(BaseModel):
    """Base output model for all AI agents."""
    reasoning_steps: list[ReasoningStep]
    citations: list[Citation]
    confidence: float  # 0.0 - 1.0
    metadata: OutputMetadata

class InvestigationResponse(AgentOutput):
    summary: str
    entities_identified: list[Entity]
    leads: list[Lead]
    timeline_events: list[TimelineEvent]
    network_data: Optional[NetworkGraph]
    financial_trail: Optional[FinancialTrail]

class HypothesisEvaluation(AgentOutput):
    hypothesis: str
    supporting_evidence: list[Evidence]
    contradicting_evidence: list[Evidence]
    missing_evidence: list[str]
    verdict: Literal["supported", "contradicted", "inconclusive"]
```

### Token Budget Management

```python
DAILY_TOKEN_BUDGETS = {
    "groq": 2_000_000,       # Free tier daily limit
    "gemini": 5_000_000,     # Generous fallback pool
    "mistral": 1_000_000,    # Secondary fallback
    "openrouter": 500_000,   # Emergency only
}

# Per-request limits
MAX_INPUT_TOKENS = 8_000    # User query + context
MAX_OUTPUT_TOKENS = 4_000   # Response generation
MAX_CONTEXT_WINDOW = 32_000 # Retrieved context + history
```

Budget tracking via Redis counters, reset at midnight IST. Alerts at 80% consumption.

### Streaming SSE Delivery

```python
async def stream_investigation_response(query: str, session_id: str):
    """Stream response tokens via Server-Sent Events."""
    async for chunk in litellm.acompletion(
        model="investigateai-primary",
        messages=messages,
        stream=True,
        response_format=InvestigationResponse,
    ):
        yield ServerSentEvent(
            event="token",
            data=json.dumps({
                "chunk": chunk.choices[0].delta.content,
                "session_id": session_id,
                "timestamp": datetime.now(IST).isoformat()
            })
        )
    yield ServerSentEvent(event="done", data=json.dumps({"status": "complete"}))
```

---

## API and Internal AI Communication Contract

The system deliberately separates external application communication from internal AI communication.

### External boundary

- Catalyst API Gateway is the public entry point for authentication, RBAC, throttling, and routing.
- The frontend uses capability-oriented REST APIs for investigation actions and resource REST APIs for workspace state.
- Complex investigations use REST to create a run and SSE to stream plan, tool progress, evidence, reasoning, tokens, alerts, and completion.
- Simple lookups may return synchronously through REST.
- Voice and document inputs use multipart REST.
- WebSockets are deferred until collaborative multi-investigator editing or presence is required.

### Internal AI boundary

- LangGraph is the orchestrator and calls a typed Python Tool Registry directly.
- Tools, not agents, access the Data Store, pgvector, Neo4j, ONNX models, Stratus, and intelligence cards.
- Tool inputs and outputs are Pydantic models with authorization context, query limits, citations, and audit metadata.
- gRPC is reserved for a future split into independent internal services; it is not part of the initial Catalyst deployment.
- MCP is an optional adapter for interoperability with external agent clients; it is not required for runtime orchestration.

### Capability API examples

```http
POST /api/v1/investigations/{id}/query
POST /api/v1/investigations/{id}/network-analysis
POST /api/v1/investigations/{id}/profile-offender
POST /api/v1/investigations/{id}/similar-cases
POST /api/v1/investigations/{id}/hypothesis
POST /api/v1/investigations/{id}/generate-report
```

### Internal execution path

```text
Frontend
  ↓ REST capability/resource API
Catalyst API Gateway
  ↓
Capability API / BFF
  ↓
LangGraph Investigation Engine
  ↓ direct typed calls
Internal Tool Registry
  ↓
SQL + pgvector + Neo4j + intelligence cards + LLM services
  ↓
SSE event stream back to the workspace
```

---

## Retrieval Strategy (4-Way Hybrid)

### Architecture Overview

```
User Query
    │
    ├──► SQL Retriever ──────────────────────────────────────┐
    ├──► Vector Retriever ───────────────────────────────────┤
    ├──► Graph Retriever ────────────────────────────────────┤
    └──► Keyword Retriever ──────────────────────────────────┤
                                                             ▼
                                                   Reciprocal Rank Fusion (k=60)
                                                             │
                                                             ▼
                                                   BGE-Reranker-v2-m3 (top-20 → top-5)
                                                             │
                                                             ▼
                                                   Annotated Results + Citations
```

### SQL Retriever

Structured filters for deterministic queries:

```sql
SELECT f.fir_id, f.narrative, f.district, f.date_filed, f.status
FROM firs f
JOIN fir_ipc_sections fis ON f.fir_id = fis.fir_id
WHERE f.district = :district
  AND f.date_filed BETWEEN :start_date AND :end_date
  AND fis.ipc_section = ANY(:ipc_sections)
  AND f.status = :status
ORDER BY f.date_filed DESC
LIMIT 50;
```

**Handles:** "Show me all theft cases in Bengaluru Urban from January 2025 that are still under investigation"

### Vector Retriever

Semantic similarity on narrative embeddings:

```sql
CREATE INDEX idx_fir_embedding_hnsw ON fir_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);

SELECT f.fir_id, f.narrative, 1 - (fe.embedding <=> :query_embedding) AS similarity
FROM fir_embeddings fe
JOIN firs f ON fe.fir_id = f.fir_id
WHERE 1 - (fe.embedding <=> :query_embedding) > 0.65
ORDER BY fe.embedding <=> :query_embedding
LIMIT 50;
```

**Handles:** "Cases involving someone being lured through a matrimonial website and extorted" (semantic match, not keyword)

### Graph Retriever

Neo4j Cypher patterns for relationship traversal:

```cypher
// N-hop traversal: Find all entities connected to a suspect within 3 hops
MATCH path = (s:Person {name: $suspect_name})-[*1..3]-(connected)
WHERE ALL(r IN relationships(path) WHERE r.confidence > 0.6)
RETURN connected, relationships(path), length(path) AS hops
ORDER BY hops ASC, connected.pagerank DESC
LIMIT 50;

// Path queries: How are two entities connected?
MATCH path = shortestPath(
  (a:Person {entity_id: $entity_a})-[*..5]-(b:Person {entity_id: $entity_b})
)
RETURN path, [r IN relationships(path) | type(r)] AS relationship_types;
```

**Handles:** "Show me everyone connected to Rajesh Kumar within 3 degrees" / "How is suspect A related to suspect B?"

### Keyword Retriever

PostgreSQL full-text search for exact term matching:

```sql
CREATE INDEX idx_fir_narrative_fts ON firs USING gin(narrative_tsv);

SELECT f.fir_id, f.narrative,
       ts_rank_cd(f.narrative_tsv, plainto_tsquery('english', :query)) AS rank
FROM firs f
WHERE f.narrative_tsv @@ plainto_tsquery('english', :query)
ORDER BY rank DESC
LIMIT 50;
```

**Handles:** Exact names, specific locations, vehicle numbers, phone numbers, FIR references

### Fusion: Reciprocal Rank Fusion (RRF)

```python
def reciprocal_rank_fusion(result_lists: list[list[Result]], k: int = 60) -> list[Result]:
    """
    Merge results from all 4 retrievers using RRF.
    
    RRF Score = Σ (1 / (k + rank_i)) for each list where document appears
    k=60 balances top-ranked vs. broadly-ranked results.
    """
    scores: dict[str, float] = defaultdict(float)
    result_map: dict[str, Result] = {}
    
    for result_list in result_lists:
        for rank, result in enumerate(result_list, start=1):
            scores[result.id] += 1.0 / (k + rank)
            result_map[result.id] = result
    
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [result_map[doc_id] for doc_id, _ in fused[:20]]
```

### Reranking: BGE-Reranker-v2-m3

```python
from FlagEmbedding import FlagReranker

reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)

def rerank_results(query: str, candidates: list[Result], top_k: int = 5) -> list[Result]:
    """Score top-20 RRF results → return top-5 with reranker confidence."""
    pairs = [[query, candidate.text] for candidate in candidates]
    scores = reranker.compute_score(pairs, normalize=True)
    
    scored_results = sorted(
        zip(candidates, scores), key=lambda x: x[1], reverse=True
    )
    return [
        Result(**result.dict(), reranker_score=score, retrieval_source=result.source)
        for result, score in scored_results[:top_k]
    ]
```

### Citations

Every result annotated with provenance:

```python
class Citation(BaseModel):
    source_fir_id: str          # e.g., "KA/BLR/2025/001234"
    entity_id: Optional[str]    # e.g., "ENT-00456"
    confidence: float           # Reranker score (0.0 - 1.0)
    retrieval_source: Literal["sql", "vector", "graph", "keyword"]
    text_span: str              # Exact quoted text from source
    page_reference: Optional[str]
```

---

## Embedding Pipeline

### Offline Batch Embedding

```python
EMBEDDING_CONFIG = {
    "model": "BAAI/bge-m3",
    "quantization": "INT8",
    "runtime": "ONNX",
    "dimensions": 1024,
    "sparse_weights": True,
    "batch_size": 256,
    "total_firs": 50_000,
    "total_entities": 200_000,
}

async def batch_embed_corpus():
    """Nightly job: Re-embed new/updated FIRs and entities."""
    new_firs = await get_unembedded_firs()
    
    for batch in chunked(new_firs, EMBEDDING_CONFIG["batch_size"]):
        embeddings = model.encode(
            [fir.narrative for fir in batch],
            return_dense=True,
            return_sparse=True,
        )
        await store_embeddings(batch, embeddings)
```

### Online Query Embedding

```python
async def embed_and_retrieve(query: str) -> list[Result]:
    """Real-time: Embed user query → retrieve → rerank."""
    query_embedding = model.encode(query, return_dense=True, return_sparse=True)
    
    results = await asyncio.gather(
        sql_retriever.retrieve(query),
        vector_retriever.retrieve(query_embedding.dense),
        graph_retriever.retrieve(query),
        keyword_retriever.retrieve(query, sparse_weights=query_embedding.sparse),
    )
    
    fused = reciprocal_rank_fusion(results, k=60)
    reranked = rerank_results(query, fused, top_k=5)
    return reranked
```

### Model: BGE-M3 INT8 ONNX

| Property | Value |
|----------|-------|
| Model | BAAI/bge-m3 |
| Quantization | INT8 (ONNX Runtime) |
| Dense Dimensions | 1024 |
| Sparse Weights | Learned term importance (lexical) |
| Max Sequence Length | 8192 tokens |
| Inference Device | CPU (ONNX optimized) |
| Throughput | ~500 docs/sec (batch) |
| Languages | Multilingual (English, Hindi, Kannada) |

---

## Intelligence Engines (Pre-computed)

All engines run as scheduled background tasks, storing results as pre-computed intelligence cards accessible instantly at query time.

### NetworkDetectionEngine

```python
class NetworkDetectionEngine:
    """Daily Cron → Louvain + PageRank + Betweenness → NetworkIntelligenceCards"""
    
    schedule: str = "0 2 * * *"  # 2 AM IST daily
    
    async def run(self):
        graph = await self.extract_entity_graph()
        communities = nx.community.louvain_communities(graph, resolution=1.2)
        pagerank = nx.pagerank(graph, alpha=0.85)
        betweenness = nx.betweenness_centrality(graph, normalized=True)
        
        cards = []
        for community_id, members in enumerate(communities):
            if len(members) >= 3:
                cards.append(NetworkIntelligenceCard(
                    community_id=community_id,
                    members=members,
                    key_players=self.identify_key_players(members, pagerank, betweenness),
                    risk_score=self.compute_network_risk(members),
                    active_cases=self.get_active_cases(members),
                    geographic_spread=self.compute_spread(members),
                ))
        
        await self.store_stratus_json(cards)
```

**Output:** `NetworkIntelligenceCards` → Stratus JSON format for frontend visualization

### PatternForecastEngine

```python
class PatternForecastEngine:
    """Daily Cron → Prophet per (district, category) + H3 hotspots → HotspotCards"""
    
    schedule: str = "0 3 * * *"  # 3 AM IST daily
    
    async def run(self):
        for district in KARNATAKA_DISTRICTS:
            for category in CRIME_CATEGORIES:
                ts_data = await self.get_time_series(district, category)
                model = Prophet(seasonality_mode='multiplicative')
                model.fit(ts_data)
                forecast = model.predict(future_periods=30)
                
                hotspots = await self.compute_h3_hotspots(district, category)
                
                card = HotspotCard(
                    district=district,
                    category=category,
                    forecast_trend=forecast.trend,
                    predicted_count_7d=forecast.yhat[:7].sum(),
                    hotspot_hexagons=hotspots,
                    confidence_interval=forecast.yhat_upper - forecast.yhat_lower,
                    seasonality_patterns=self.extract_patterns(model),
                )
                await self.store_card(card)
```

**Output:** `HotspotCards` → 30-day crime forecasts per district/category + H3 hex hotspot maps

### BehavioralProfileEngine

```python
class BehavioralProfileEngine:
    """Daily Cron → per-offender history analysis → OffenderProfiles"""
    
    schedule: str = "0 4 * * *"  # 4 AM IST daily
    
    async def run(self):
        active_offenders = await self.get_active_offenders()
        
        for offender in active_offenders:
            history = await self.get_full_history(offender.entity_id)
            
            profile = OffenderProfile(
                entity_id=offender.entity_id,
                modus_operandi_patterns=self.extract_mo_patterns(history),
                geographic_patterns=self.extract_geo_patterns(history),
                temporal_patterns=self.extract_time_patterns(history),
                associate_network=self.get_associates(offender.entity_id),
                escalation_risk=self.compute_escalation_risk(history),
                recidivism_score=self.compute_recidivism(history),
                last_known_activity=history[-1] if history else None,
            )
            await self.store_profile(profile)
```

**Output:** `OffenderProfiles` → Behavioral patterns, risk scores, associate networks

### FinancialLinkEngine

```python
class FinancialLinkEngine:
    """Daily Cron → UPI/Account subgraph analysis → FinancialTrails"""
    
    schedule: str = "0 5 * * *"  # 5 AM IST daily
    
    async def run(self):
        financial_graph = await self.extract_financial_subgraph()
        
        patterns = self.detect_patterns(financial_graph)
        # - Layering (rapid transfers through multiple accounts)
        # - Structuring (amounts just below reporting threshold)
        # - Circular flows (money returning to origin)
        # - Mule accounts (high fan-in/fan-out)
        
        for pattern in patterns:
            trail = FinancialTrail(
                trail_id=generate_id(),
                accounts_involved=pattern.accounts,
                total_amount=pattern.total_flow,
                pattern_type=pattern.type,
                risk_score=pattern.risk,
                linked_firs=self.get_linked_firs(pattern.accounts),
                sankey_data=self.generate_sankey(pattern),
            )
            await self.store_trail(trail)
```

**Output:** `FinancialTrails` → UPI/Account flow analysis + Sankey diagram data

### SimilarCaseEngine

```python
class SimilarCaseEngine:
    """On FIR insert (Signal) → compute similarity → index"""
    
    trigger: str = "signal:fir_inserted"  # Event-driven, not cron
    
    async def on_fir_inserted(self, new_fir: FIR):
        embedding = model.encode(new_fir.narrative, return_dense=True)
        
        similar = await vector_retriever.find_similar(
            embedding=embedding.dense,
            threshold=0.75,
            limit=10,
            exclude_id=new_fir.fir_id,
        )
        
        scored_similar = []
        for case in similar:
            score = SimilarityScore(
                narrative_similarity=case.cosine_score,
                entity_overlap=self.compute_entity_overlap(new_fir, case),
                mo_similarity=self.compute_mo_match(new_fir, case),
                geographic_proximity=self.compute_geo_distance(new_fir, case),
                temporal_proximity=self.compute_time_distance(new_fir, case),
                composite_score=self.weighted_composite(...)
            )
            scored_similar.append((case, score))
        
        await self.store_similarities(new_fir.fir_id, scored_similar)
        await self.check_active_investigations(new_fir, scored_similar)
```

**Output:** Similarity index updated on every new FIR insertion. Alerts triggered for active investigations.

---

## Explainability

### ReasoningStep Dataclass

```python
@dataclass
class ReasoningStep:
    """Atomic unit of AI reasoning — fully traceable."""
    step_type: Literal[
        "retrieval", "inference", "deduction", 
        "hypothesis", "comparison", "aggregation"
    ]
    description: str                    # Human-readable step description
    input_evidence: list[Citation]      # What evidence was used
    reasoning: str                      # How the conclusion was reached
    confidence: float                   # 0.0 - 1.0
    supporting_facts: list[str]         # Facts that support this step
    contradicting_facts: list[str]      # Facts that contradict this step
    timestamp: datetime                 # When this step was executed
```

### ExplainabilityPackage

```python
@dataclass
class ExplainabilityPackage:
    """Complete explanation of how AI reached its conclusion."""
    query: str                              # Original user query
    reasoning_trace: list[ReasoningStep]    # Full chain of reasoning
    citations: list[Citation]               # All sources used
    alternatives_considered: list[str]      # Other interpretations explored
    missing_evidence: list[str]             # What would strengthen/change conclusion
    confidence_breakdown: dict[str, float]  # Per-component confidence
    total_confidence: float                 # Overall confidence
    
    def to_officer_summary(self) -> str:
        """Generate officer-friendly explanation."""
        ...
    
    def to_audit_log(self) -> dict:
        """Generate compliance audit trail."""
        ...
```

### Grounding Policy

```
RULE: Every claim → source record. No ungrounded assertions.

Implementation:
1. Every sentence in AI output MUST have ≥1 Citation
2. If no source exists → explicitly state "No evidence found for..."
3. Confidence < 0.5 → prefix with "Low confidence: ..."
4. Contradictions → surface both sides, never suppress
5. Audit log stores full ExplainabilityPackage for every query
```

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KSP InvestigateAI                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌────────────────┐    ┌───────────────────────┐  │
│  │   Frontend   │───►│ Catalyst API   │───►│ LangGraph + Tool      │  │
│  │  (React/Slate)│◄──│ Gateway + SSE  │◄──│ Registry + LiteLLM    │  │
│  └─────────────┘    └──────────────┘    └───────────┬───────────┘  │
│                                                      │              │
│  ┌───────────────────────────────────────────────────┼───────────┐  │
│  │              4-Way Hybrid Retrieval               │           │  │
│  │  ┌─────┐  ┌────────┐  ┌───────┐  ┌─────────┐   │           │  │
│  │  │ SQL │  │ Vector │  │ Graph │  │ Keyword │   │           │  │
│  │  └──┬──┘  └───┬────┘  └───┬───┘  └────┬────┘   │           │  │
│  │     └──────────┴───────────┴────────────┘        │           │  │
│  │                    │                              │           │  │
│  │              RRF (k=60)                           │           │  │
│  │                    │                              │           │  │
│  │         BGE-Reranker-v2-m3                        │           │  │
│  │              (top-5)                              │           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │            Pre-computed Intelligence Engines                   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │  │
│  │  │ Network  │ │ Pattern  │ │Behavioral│ │Financial │        │  │
│  │  │Detection │ │ Forecast │ │ Profile  │ │  Links   │        │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │  │
│  │                    ┌──────────┐                               │  │
│  │                    │ Similar  │                               │  │
│  │                    │  Cases   │ (Event-driven)                │  │
│  │                    └──────────┘                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Data Stores                                       │  │
│  │  ┌────────────┐  ┌──────────┐  ┌───────┐  ┌──────────────┐  │  │
│  │  │ PostgreSQL │  │ pgvector │  │ Neo4j │  │    Redis     │  │  │
│  │  │  (FIRs +   │  │(Embeddings│  │(Graph)│  │(Cache+Budget)│  │  │
│  │  │   FTS)     │  │ 1024-d)  │  │       │  │              │  │  │
│  │  └────────────┘  └──────────┘  └───────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
