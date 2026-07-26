<!-- Runtime amendment: Hexel owns platform orchestration; KSP owns investigation intelligence. The temporary Runner only passes InvestigationState through Strands agents. -->
# The Investigation Engine Core
> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24


> KSP InvestigateAI — Investigation Intelligence System
> Last Updated: 2026-07-23

---

## Case Memory (Persistent State)

### Catalyst-compatible checkpoint adapter

Investigation state survives across sessions through a Catalyst-compatible investigation-service checkpoint adapter backed by Catalyst Data Store, with Catalyst Cache for hot session state. This adapter is the locked deployment direction and must be validated against Catalyst APIs.

```python
class CatalystCheckpointAdapter:
    async def put(self, thread_id: str, state: dict) -> None:
        # Versioned checkpoint written through the Catalyst SDK.
        ...

    async def get(self, thread_id: str) -> dict | None:
        # Cache first, then Catalyst Data Store.
        ...

checkpointer = CatalystCheckpointAdapter()
# P09 investigation service uses this boundary; the Runner does not own persistence.
```

For local development, P09 provides a local checkpoint adapter with the same application contract. A PostgreSQL saver is not a deployment dependency.

### Session Continuity

```python
async def resume_investigation(officer_id: str, investigation_id: str):
    """Officer returns → restore full investigation context."""
    config = {"configurable": {"thread_id": f"{officer_id}:{investigation_id}"}}
    
    # Restore state from last checkpoint
    state = await app.aget_state(config)
    
    # Generate context briefing
    briefing = f"""
    Welcome back, Officer. Here's your investigation status:
    - Active Cases: {len(state.values['active_case_ids'])} FIRs
    - Pinned Entities: {len(state.values['pinned_entities'])} on evidence board
    - Active Hypotheses: {len(state.values['hypotheses'])}
    - Open Leads: {len([l for l in state.values['leads'] if l.status == 'open'])}
    - Last Activity: {state.values['last_activity'].strftime('%d %b %Y, %I:%M %p')}
    - Last Query: "{state.values['last_query']}"
    """
    return briefing, state
```

---

## Orchestrated investigation flow

The InvestigationService routes requests through the Runner when an agent workflow is required; it is not an LLM agent. It restores case memory, classifies the request, and selects:

- **Fast path:** exact/structured query → deterministic SQL Retrieval, Search/Ranking, Graph Intelligence, or Timeline Engine → Evidence/Explainability gate → cited response; no LLM when unnecessary.
- **Deep path:** optional Planner Agent → parallel deterministic engines (SQL, search, graph, pattern, behavioral, financial, forecasting, timeline) → evidence reconciliation/gate → Reasoning Agent → deterministic Lead Ranking Engine → Reporter Agent for communication or package wording.

Tools T01–T23 are typed internal registry entries that invoke engines; they are not public routes and engines are not agents. The gate validates citations, numbers, permissions, contradictions, confidence, and missing evidence before release. Humans review consequential conclusions.

## Hypothesis Mode

### Structured Evaluation (Not Yes/No)

Officer asks: "Could X be linked to Y?" — AI evaluates with structured reasoning:

```python
class HypothesisEvaluation(BaseModel):
    """Structured hypothesis evaluation — never a simple yes/no."""
    hypothesis: str
    
    # Supporting evidence
    supporting_evidence: list[Evidence]
    supporting_strength: float  # 0.0 - 1.0
    
    # Contradicting evidence
    contradicting_evidence: list[Evidence]
    contradiction_strength: float  # 0.0 - 1.0
    
    # Overall assessment
    confidence_percentage: float  # 0-100%
    verdict: Literal["strongly_supported", "weakly_supported", "inconclusive", 
                     "weakly_contradicted", "strongly_contradicted"]
    
    # What's missing
    missing_evidence: list[MissingEvidence]
    suggested_actions: list[str]  # What to investigate next
    
    # Explainability
    structured_rationale: list[ReasoningStep]
    alternative_explanations: list[str]

class MissingEvidence(BaseModel):
    description: str
    importance: Literal["critical", "high", "medium"]
    how_to_obtain: str
    impact_if_found: str  # How it would change the evaluation
```

### Hypothesis Workflow

```python
async def evaluate_hypothesis(state: InvestigationState, hypothesis: str):
    """
    Full hypothesis evaluation pipeline.
    
    Example: "Could Rajesh Kumar (suspect in FIR-2025-001) be linked to 
              the Jayanagar ATM fraud ring?"
    """
    # 1. Retrieve all evidence related to both sides
    entity_a_evidence = await retrieve_entity_context(hypothesis.entity_a)
    entity_b_evidence = await retrieve_entity_context(hypothesis.entity_b)
    
    # 2. Graph traversal — find connection paths
    paths = await graph_retriever.find_paths(
        entity_a=hypothesis.entity_a,
        entity_b=hypothesis.entity_b,
        max_hops=5
    )
    
    # 3. Temporal overlap analysis
    temporal_links = analyze_temporal_overlap(entity_a_evidence, entity_b_evidence)
    
    # 4. Geographic co-occurrence
    geo_links = analyze_geographic_proximity(entity_a_evidence, entity_b_evidence)
    
    # 5. Financial connections
    financial_links = await financial_engine.find_connections(
        hypothesis.entity_a, hypothesis.entity_b
    )
    
    # 6. LLM reasoning over all evidence
    evaluation = await llm_evaluate(
        hypothesis=hypothesis,
        supporting=[paths, temporal_links, geo_links, financial_links],
        all_evidence=[entity_a_evidence, entity_b_evidence],
    )
    
    # 7. Store hypothesis in investigation state
    state["hypotheses"].append(evaluation)
    
    return evaluation
```

---

## Investigation Packages (Multi-Artifact Output)

Every investigation query produces a complete package, not just text:

```python
class InvestigationPackage(BaseModel):
    """Multi-artifact output for comprehensive investigation support."""
    
    # 1. Summary (structured, cited)
    summary: CitedSummary
    
    # 2. Timeline (chronological events with entity links)
    timeline: list[TimelineEvent]
    
    # 3. Network Graph (Cytoscape data format)
    network_graph: CytoscapeGraph
    
    # 4. Financial Trail (Sankey data)
    financial_trail: Optional[SankeyData]
    
    # 5. Leads (prioritized, actionable, evidence-backed)
    leads: list[Lead]
    
    # 6. Similar Cases (top-3 with overlap explanation)
    similar_cases: list[SimilarCase]
    
    # 7. PDF Report (generated on demand)
    report_url: Optional[str]

class CitedSummary(BaseModel):
    """Every sentence linked to source evidence."""
    paragraphs: list[CitedParagraph]
    key_findings: list[str]
    risk_assessment: str
    recommended_actions: list[str]

class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str
    description: str
    entities_involved: list[str]
    source_fir_id: str
    confidence: float
    location: Optional[GeoPoint]

class CytoscapeGraph(BaseModel):
    """Cytoscape.js compatible graph data."""
    nodes: list[dict]  # {data: {id, label, type, risk_score, ...}}
    edges: list[dict]  # {data: {source, target, relationship, weight, ...}}
    layout: str = "cose"  # Default layout algorithm

class SankeyData(BaseModel):
    """Apache ECharts Sankey-compatible data."""
    nodes: list[dict]  # {name, type (account/upi/person)}
    links: list[dict]  # {source, target, value, timestamp}
    total_flow: float
    suspicious_paths: list[list[int]]
```

### PDF Report Generation

```python
async def generate_pdf_report(package: InvestigationPackage) -> str:
    """Generate professional PDF report using WeasyPrint."""
    html_content = render_template("investigation_report.html", package=package)
    
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf(
        stylesheets=["report_styles.css"],
        presentational_hints=True,
    )
    
    report_url = await upload_to_secure_storage(pdf_bytes, package.investigation_id)
    return report_url
```

---

## Evidence Board

### Pinning & Continuous Reasoning

Officers pin entities/FIRs to their investigation. AI continuously reasons over pinned items.

```python
class PinnedEntity(BaseModel):
    entity_id: str
    entity_type: Literal["person", "vehicle", "phone", "account", "location", "fir"]
    pinned_at: datetime
    pinned_by: str  # Officer ID
    notes: Optional[str]
    alert_on_new_activity: bool = True

class EvidenceBoard:
    """Persistent evidence board with continuous AI reasoning."""
    
    async def pin_entity(self, entity_id: str, investigation_id: str):
        """Pin an entity to the investigation board."""
        entity = await self.resolve_entity(entity_id)
        pinned = PinnedEntity(
            entity_id=entity_id,
            entity_type=entity.type,
            pinned_at=datetime.now(IST),
            pinned_by=self.current_officer_id,
            alert_on_new_activity=True,
        )
        self.state["pinned_entities"].append(pinned)
        
        # Trigger reasoning over new pin + existing pins
        await self.reason_over_board()
    
    async def reason_over_board(self):
        """AI reasons over all pinned items — finds connections, gaps, patterns."""
        pinned = self.state["pinned_entities"]
        
        # Cross-reference all pinned entities
        connections = await graph_retriever.find_connections_among(
            [p.entity_id for p in pinned]
        )
        
        # Identify evidence gaps
        gaps = self.identify_gaps(pinned, connections)
        
        # Generate new leads from board analysis
        new_leads = await self.generate_leads_from_board(pinned, connections, gaps)
        
        return BoardInsights(
            connections=connections,
            gaps=gaps,
            new_leads=new_leads,
            updated_hypotheses=self.update_hypotheses(connections),
        )
```

### Real-Time Alerts (Signal-Driven)

```python
class EvidenceBoardAlertSystem:
    """New FIR arrives → Signal → check if it matches pinned entities → alert officer."""
    
    async def on_fir_inserted(self, new_fir: FIR):
        """Triggered by signal:fir_inserted event."""
        # Get all active evidence boards
        active_boards = await self.get_active_investigations()
        
        for board in active_boards:
            pinned_entity_ids = [p.entity_id for p in board.pinned_entities]
            
            # Check entity overlap
            fir_entities = await extract_entities(new_fir)
            overlap = set(fir_entities) & set(pinned_entity_ids)
            
            if overlap:
                # Generate alert
                alert = InvestigationAlert(
                    investigation_id=board.investigation_id,
                    officer_id=board.officer_id,
                    alert_type="new_fir_match",
                    severity="high",
                    message=f"New FIR {new_fir.fir_id} involves pinned entities: {overlap}",
                    new_fir_id=new_fir.fir_id,
                    matched_entities=list(overlap),
                    timestamp=datetime.now(IST),
                )
                await self.send_alert(alert)  # Push notification + in-app alert
```

---

## Lead Generation

### Evidence-Gap Reasoning

```python
class LeadRankingEngine:
    """Deterministically rank evidence-backed leads; optional LLM explanation is downstream."""
    
    async def generate_leads(self, state: InvestigationState) -> list[Lead]:
        """Analyze current evidence → identify gaps → generate prioritized leads."""
        
        # What do we know?
        known_evidence = state["evidence_collected"]
        pinned_entities = state["pinned_entities"]
        hypotheses = state["hypotheses"]
        
        # What's missing?
        evidence_gaps = self.identify_evidence_gaps(known_evidence, hypotheses)
        
        leads = []
        for gap in evidence_gaps:
            lead = Lead(
                lead_id=generate_id(),
                priority=self.assess_priority(gap),
                action=gap.suggested_action,
                evidence=gap.related_evidence,
                expected_outcome=gap.expected_outcome,
                confidence=gap.confidence,
                reasoning=gap.structured_rationale,
                status="open",
                generated_at=datetime.now(IST),
            )
            leads.append(lead)
        
        return sorted(leads, key=lambda l: l.priority_score, reverse=True)

class Lead(BaseModel):
    lead_id: str
    priority: Literal["critical", "high", "medium"]
    action: str              # What to do: "Obtain CDR for +91-XXXXX for Jan 2025"
    evidence: list[Citation] # Why this lead exists
    expected_outcome: str    # What finding this would reveal
    confidence: float        # How likely this lead will produce results
    reasoning: list[ReasoningStep]  # How AI arrived at this lead
    status: Literal["open", "in_progress", "completed", "dismissed"]
    generated_at: datetime
```

### Priority Classification

```python
PRIORITY_RULES = {
    "critical": {
        "description": "Act now — time-sensitive, high-impact",
        "criteria": [
            "Evidence may be destroyed/lost if not collected immediately",
            "Suspect may flee jurisdiction",
            "Active threat to victim safety",
            "Matches pattern of escalating serial offender",
        ],
        "response_time": "Within 4 hours",
    },
    "high": {
        "description": "Investigate soon — important for case progression",
        "criteria": [
            "Key connection between suspects not yet verified",
            "Financial trail going cold (account closure pending)",
            "Witness available but may become unreachable",
            "Strong hypothesis needs one more piece of evidence",
        ],
        "response_time": "Within 24 hours",
    },
    "medium": {
        "description": "Verify when possible — strengthens case",
        "criteria": [
            "Corroborating evidence for existing findings",
            "Background verification of peripheral entities",
            "Historical pattern confirmation",
            "Cross-jurisdictional records request",
        ],
        "response_time": "Within 72 hours",
    },
}
```

---

## Decision Support: Deterministic Lead Ranking

### Similar Past Cases with Outcomes

```python
class LeadRankingEngine:
    """Rank evidence-based leads and similar-case signals for investigator review."""
    
    async def get_similar_cases_with_outcomes(
        self, current_case: InvestigationState
    ) -> list[SimilarCaseOutcome]:
        """Find similar past cases and their outcomes for decision guidance."""
        
        similar = await similar_case_engine.find_similar(
            narrative=current_case.summary,
            entities=current_case.pinned_entities,
            crime_type=current_case.crime_category,
            top_k=5,
        )
        
        outcomes = []
        for case in similar:
            outcome = SimilarCaseOutcome(
                fir_id=case.fir_id,
                similarity_score=case.composite_score,
                overlap_explanation=case.explain_overlap(),
                case_outcome=case.final_outcome,  # Convicted, acquitted, pending
                time_to_resolution=case.resolution_time,
                key_evidence_that_led_to_outcome=case.decisive_evidence,
                lessons_applicable=self.extract_lessons(case, current_case),
            )
            outcomes.append(outcome)
        
        return outcomes
```

### Risk Scoring

```python
class RiskScorer:
    """Multi-dimensional risk scoring for investigation prioritization."""
    
    async def compute_risk(self, investigation: InvestigationState) -> RiskScore:
        """Compute risk signal: offender + location + time."""
        
        # Offender risk (recidivism, escalation pattern, network centrality)
        offender_risk = await self.score_offender_risk(
            investigation.primary_suspects
        )
        
        # Location risk (historical crime density, current hotspot status)
        location_risk = await self.score_location_risk(
            investigation.crime_location
        )
        
        # Temporal risk (time since last activity, seasonal patterns)
        temporal_risk = await self.score_temporal_risk(
            investigation.timeline
        )
        
        return RiskScore(
            overall=self.weighted_average(offender_risk, location_risk, temporal_risk),
            offender_component=offender_risk,
            location_component=location_risk,
            temporal_component=temporal_risk,
            confidence=self.score_confidence(),
            factors=self.explain_factors(),
        )
```

### Recommended Next Actions

```python
class ActionRecommender:
    """Recommend next actions based on investigation stage."""
    
    INVESTIGATION_STAGES = [
        "initial_report",       # FIR just filed
        "evidence_collection",  # Gathering evidence
        "suspect_identification", # Identifying suspects
        "network_mapping",      # Mapping criminal network
        "case_building",        # Building prosecution case
        "pre_chargesheet",      # Preparing chargesheet
    ]
    
    async def recommend(self, state: InvestigationState) -> list[Recommendation]:
        """Generate stage-appropriate action recommendations."""
        
        current_stage = self.detect_stage(state)
        
        recommendations = []
        
        # Stage-specific recommendations
        stage_actions = await self.get_stage_actions(current_stage, state)
        
        # Evidence-gap-driven recommendations
        gap_actions = await self.get_gap_actions(state)
        
        # Time-sensitive recommendations
        urgent_actions = await self.get_urgent_actions(state)
        
        all_actions = stage_actions + gap_actions + urgent_actions
        
        # Deduplicate and prioritize
        recommendations = self.prioritize_and_deduplicate(all_actions)
        
        return [
            Recommendation(
                action=action.description,
                rationale=action.reasoning,
                priority=action.priority,
                evidence_basis=action.supporting_evidence,
                expected_impact=action.expected_impact,
                stage_relevance=current_stage,
            )
            for action in recommendations[:10]  # Top 10 recommendations
        ]
```

---

## System Integration Summary

```
┌─────────────────────────────────────────────────────────────┐
│                  Investigation Engine                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Officer Query ──► Investigation Service and Runner                   │
│                         │                                    │
│                    ┌────┴────┐                               │
│                    ▼         ▼                               │
│              Retrieve    Reason                               │
│                    │         │                               │
│                    ▼         ▼                               │
│              Evidence    Hypotheses                           │
│               Board       Mode                               │
│                    │         │                               │
│                    └────┬────┘                               │
│                         ▼                                    │
│              Investigation Package                            │
│              ┌──────────────────┐                            │
│              │ Summary          │                            │
│              │ Timeline         │                            │
│              │ Network Graph    │                            │
│              │ Financial Trail  │                            │
│              │ Leads            │                            │
│              │ Similar Cases    │                            │
│              │ PDF Report       │                            │
│              └──────────────────┘                            │
│                         │                                    │
│                         ▼                                    │
│        Deterministic Lead Ranking Engine                    │
│              ┌──────────────────┐                            │
│              │ Risk Signal       │                            │
│              │ Past Outcomes    │                            │
│              │ Next Actions     │                            │
│              └──────────────────┘                            │
│                                                              │
│  ◄── Signals ───────────────────────────────────────────►   │
│  New FIR → Match pinned entities → Alert officer             │
│                                                              │
│  ◄── Persistence ──────────────────────────────────────►    │
│  Catalyst checkpoint adapter → State survives across sessions    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```
