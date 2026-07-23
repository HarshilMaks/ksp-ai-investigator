# InvestigateAI — Product Requirements Document

> **Version:** 1.0 | **Status:** LOCKED | **Target:** KSP Datathon 2026 Challenge 1

---

## 1. Challenge Requirements → Feature Mapping

### Requirement 1: Conversational Crime Intelligence

**Challenge Ask:** Natural language interface for querying crime data.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Chat Interface | React + Streaming SSE | Real-time token streaming, markdown rendering |
| Voice Input | Web Speech API / Whisper | Kannada + English voice queries |
| Context Memory | Session state + vector recall | Multi-turn investigation context (last 20 turns) |
| PDF Export | React-PDF / Puppeteer | One-click Investigation Package generation |
| Query Understanding | LLM + Intent Router | Classify → route to specialized agent |

**User Flow:**
```
Officer speaks/types → Intent classified → Agent activated → 
Intelligence card rendered → Officer acts or follows up → 
Session exportable as PDF brief
```

---

### Requirement 2: Criminal Network Analysis

**Challenge Ask:** Identify and visualize criminal networks and associations.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Graph Database | Neo4j 5.x | Store criminal relationships, co-accused links, shared addresses |
| Graph Algorithms | Neo4j GDS | PageRank, Louvain community detection, betweenness centrality |
| Visualization | Cytoscape.js | Interactive network graphs with zoom, filter, expand |
| Intelligence Cards | Custom React components | Network summary: key players, communities, bridges |
| Temporal Analysis | Edge timestamps | Show network evolution over time |

**Pre-computed Intelligence:**
- Community clusters updated on data ingest
- PageRank scores for all criminals in graph
- Bridge nodes (betweenness centrality > threshold) flagged
- 2-hop expansion paths pre-cached for known offenders

---

### Requirement 3: Crime Pattern & Trend Analysis

**Challenge Ask:** Detect spatial and temporal crime patterns.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Time-Series Forecasting | Prophet (per district × category) | 30/60/90-day crime forecasts with confidence bands |
| Spatial Analysis | H3 Hexagonal Grid (resolution 7–9) | Hotspot detection, cluster identification |
| Visualization | ECharts + Deck.gl | Heatmaps, trend lines, hexagonal overlays |
| Pattern Detection | Statistical anomaly detection | Z-score deviation from expected patterns |
| Seasonality | Prophet decomposition | Weekly, monthly, festival-linked patterns |

**Intelligence Outputs:**
- "Burglary in Whitefield has increased 34% vs last quarter (p<0.05)"
- Hexagonal hotspot map with intensity gradients
- Temporal heatmap showing peak crime hours by category

---

### Requirement 4: Sociological Insights

**Challenge Ask:** Correlate crime with demographic and socioeconomic factors.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Demographic Data | Synthetic census (ward-level) | Population density, literacy, income brackets |
| Correlation Engine | Statistical analysis | Crime rate vs demographic features |
| Visualization | ECharts scatter/bubble | Multi-variate demographic-crime plots |
| Insight Cards | LLM-generated narratives | "Areas with X demographic profile show Y pattern" |
| Ethical Guardrails | Output filtering | No causal claims, correlation-only language |

**Data Sources (Synthetic):**
- Ward-level population demographics
- Literacy and employment rates
- Urbanization index
- Public infrastructure density (streetlights, CCTV coverage)

**Important:** All demographic data is synthetic/publicly available. No private citizen data used.

---

### Requirement 5: Offender Profiling

**Challenge Ask:** Build behavioral profiles for known offenders.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Behavioral Engine | Rule-based + ML scoring | MO extraction, escalation patterns |
| Risk Scoring | Multi-factor model | Recidivism probability, violence escalation |
| MO Signatures | NLP extraction from FIRs | Weapon preference, time-of-day, target type |
| Similar Offender Matching | Vector similarity | "Criminals with similar MO in jurisdiction" |
| Profile Cards | Structured UI component | One-page criminal intelligence summary |

**Profile Components:**
```
┌─────────────────────────────────────┐
│         OFFENDER PROFILE            │
├─────────────────────────────────────┤
│ Identity: Name, aliases, photo ref  │
│ MO Signature: Weapons, timing, area │
│ Network: Associates (graph link)    │
│ History: FIR timeline, escalation   │
│ Risk Score: Low/Medium/High/Critical│
│ Predictions: Likely next behavior   │
│ Similar Offenders: Top 3 matches    │
└─────────────────────────────────────┘
```

---

### Requirement 6: Investigator Decision Support

**Challenge Ask:** Provide actionable recommendations to investigating officers.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Lead Generation | Agent-driven analysis | Ranked leads with confidence scores |
| Similar Cases | Vector search on FIR embeddings | "Cases with similar pattern/MO/location" |
| Investigation Packages | Composite PDF generation | Brief + network + leads + timeline |
| Next Best Action | Rule engine + LLM | "Recommended next steps for this case" |
| Case Timeline | Event extraction from FIRs | Chronological reconstruction |

**Investigation Package Contents:**
1. Case Summary (auto-generated from FIR)
2. Criminal Network Diagram (relevant subgraph)
3. Ranked Leads (with evidence citations)
4. Similar Cases (with outcomes)
5. Recommended Actions (prioritized)
6. Evidence Checklist

---

### Requirement 7: Financial Crime Detection

**Challenge Ask:** Trace and visualize financial crime patterns.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Transaction Graph | Neo4j (account nodes, transaction edges) | UPI/bank account relationship mapping |
| Flow Visualization | Sankey Diagrams (ECharts) | Money flow from source → layers → destination |
| Layering Detection | Graph pattern matching | Identify structuring, smurfing, round-tripping |
| Anomaly Detection | Statistical thresholds | Unusual transaction volumes, velocities |
| Alert Cards | Custom components | "Suspicious pattern detected: 4 accounts, ₹X flow" |

**Detection Patterns:**
- **Structuring:** Multiple sub-threshold transactions
- **Layering:** Rapid pass-through accounts (in → out < 24h)
- **Round-tripping:** Circular flows returning to origin
- **Mule Accounts:** High fan-in/fan-out ratio with short lifespan

---

### Requirement 8: Crime Forecasting

**Challenge Ask:** Predict future crime occurrences.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Forecasting Engine | Prophet (per district × crime category) | 30-day rolling forecasts |
| Granularity | District + Category + Time | 31 districts × N categories = individual models |
| Proactive Alerts | Signals System | Push notifications when forecast exceeds threshold |
| Confidence Bands | Prophet uncertainty intervals | 80% and 95% confidence bands on predictions |
| Accuracy Tracking | MAPE / MAE metrics | Model performance monitoring |

**Signal Types:**
- 🔴 **Critical:** Forecast shows >50% increase vs baseline
- 🟡 **Warning:** Forecast shows >25% increase vs baseline
- 🟢 **Stable:** Within expected range
- 🔵 **Declining:** Forecast shows decrease — resource reallocation opportunity

---

### Requirement 9: Explainable AI

**Challenge Ask:** All AI outputs must be interpretable and trustworthy.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Reasoning Trace | Chain-of-thought logging | Step-by-step reasoning visible to user |
| Evidence Citations | Source linking | Every claim → clickable FIR/record reference |
| Confidence Scores | Calibrated probability | Low/Medium/High with numeric score |
| Uncertainty Communication | Natural language | "Based on 3 FIRs (high confidence)" vs "Limited data (low confidence)" |
| Audit Trail | Full interaction logging | What was asked, what was retrieved, what was generated |

**Citation Format:**
```
"Accused X was involved in 3 chain-snatching cases in 2024"
  └── [FIR-2024-001] [FIR-2024-047] [FIR-2024-112] ← clickable
  └── Confidence: HIGH (3 direct FIR matches)
  └── Reasoning: Name match + MO match + jurisdiction overlap
```

---

### Requirement 10: Secure Role-Based Access Control

**Challenge Ask:** Multi-level access control appropriate for law enforcement.

**Our Implementation:**

| Component | Technology | Capability |
|-----------|-----------|------------|
| Authentication | Catalyst Auth (Zoho) | SSO, session management, MFA-ready |
| Authorization | Custom claims on JWT | Role + jurisdiction encoded in token |
| Role Hierarchy | 5 levels | SHO → IO → DCP → Analyst → SP |
| Data Scoping | Query-time filtering | Each role sees only their jurisdiction |
| Audit Log | Immutable append-only log | Every query, every access, every export logged |

**Role Definitions:**

| Role | Jurisdiction Scope | Capabilities |
|------|-------------------|--------------|
| **SHO** | Single station | View station cases, generate leads, export briefs |
| **IO** | Assigned cases only | Deep investigation, full network expansion, profiling |
| **DCP** | Division (multiple stations) | Aggregate patterns, resource allocation, trends |
| **Analyst** | Assigned scope (flexible) | Cross-jurisdictional analysis, pattern detection |
| **SP** | Full district | District-wide intelligence, forecasting, oversight |

---

## 2. User Personas

### SHO — Station House Officer
- **Context:** Manages a police station, oversees all cases
- **Needs:** Quick station-level crime overview, pending leads, pattern alerts
- **Key Interaction:** "Show me this week's cases and any patterns"

### IO — Investigating Officer
- **Context:** Assigned specific cases, needs deep investigation support
- **Needs:** Criminal networks, similar cases, offender profiles, evidence packages
- **Key Interaction:** "Who are the associates of accused X and what's their MO?"

### DCP — Deputy Commissioner of Police
- **Context:** Oversees a division, makes resource allocation decisions
- **Needs:** Division-wide trends, hotspots, forecasts, performance metrics
- **Key Interaction:** "Which areas need more patrolling next week?"

### Analyst
- **Context:** Intelligence analyst, works across jurisdictions
- **Needs:** Cross-case pattern detection, network analysis, financial trails
- **Key Interaction:** "Find all cases linked to this phone number/vehicle/MO"

### SP — Superintendent of Police
- **Context:** District head, strategic oversight
- **Needs:** District dashboard, forecasts, sociological insights, audit oversight
- **Key Interaction:** "District crime forecast for next month with resource recommendations"

---

## 3. Scope Freeze — 5 Demo Scenarios

> **These are the ONLY scenarios we build and demonstrate. No scope creep.**

### Scenario 1: Serial Chain-Snatching Investigation
- **Trigger:** IO queries about a chain-snatching series in Koramangala
- **Demonstrates:** Req 1 (Chat), Req 5 (Profiling), Req 6 (Decision Support), Req 9 (Explainability)
- **Output:** Offender profile + similar cases + ranked leads + investigation package

### Scenario 2: Criminal Network Exposure
- **Trigger:** "Show me the network of accused Rajesh Kumar"
- **Demonstrates:** Req 2 (Network Analysis), Req 5 (Profiling), Req 9 (Explainability)
- **Output:** Interactive network graph + community detection + key player identification

### Scenario 3: Crime Hotspot Forecasting
- **Trigger:** DCP asks "Where should I deploy resources next week?"
- **Demonstrates:** Req 3 (Patterns), Req 8 (Forecasting), Req 4 (Sociological)
- **Output:** H3 hexagonal hotspot map + Prophet forecast + demographic context

### Scenario 4: Financial Fraud Trail
- **Trigger:** "Trace the money flow from account ending 4521"
- **Demonstrates:** Req 7 (Financial Crime), Req 2 (Network), Req 9 (Explainability)
- **Output:** Sankey flow diagram + layering detection + flagged mule accounts

### Scenario 5: District Intelligence Briefing
- **Trigger:** SP requests monthly intelligence summary
- **Demonstrates:** Req 3 (Trends), Req 8 (Forecasting), Req 4 (Sociological), Req 10 (RBAC)
- **Output:** PDF briefing package + forecast + resource recommendations + audit trail

---

## 4. Non-Goals

| We Are NOT Building | Why |
|--------------------|-----|
| A dashboard replacement | Officers have dashboards. They need intelligence, not more charts. |
| A CCTNS replacement | CCTNS is the system of record. We layer intelligence ON TOP. |
| Real-time surveillance | No live camera feeds, no phone tracking, no real-time location. |
| A general chatbot | Every response must be investigation-specific, not generic AI. |
| Data entry system | We consume data, we don't replace the FIR filing process. |
| Mobile app | Web-first for datathon. Mobile is Phase 2. |

---

## 5. MVP Definition

**The MVP is complete when:**

✅ All 10 challenge requirements are implemented with at least one feature each  
✅ All 5 demo scenarios execute end-to-end without manual intervention  
✅ P99 retrieval latency < 200ms (pre-computed intelligence)  
✅ Every AI output has citations traceable to source records  
✅ RBAC enforces role-based data scoping (demo with 2+ roles)  
✅ Investigation Package (PDF) generates in < 5 seconds  
✅ Voice input works for at least English queries  
✅ Network visualization renders graphs with 50+ nodes interactively  
✅ Forecast models produce district × category predictions with confidence bands  
✅ Full audit log captures all interactions  

---

## 6. Technical Constraints

| Constraint | Decision |
|-----------|----------|
| Hosting | Zoho Catalyst (mandated by challenge) |
| Auth | Catalyst Auth with custom claims |
| Database | Catalyst Datastore + Neo4j (self-hosted or AuraDB) |
| LLM | Catalyst AI / OpenAI API (with fallback) |
| Frontend | React + TypeScript (SPA) |
| Backend | Node.js Catalyst Functions |
| Vector Store | Embedded (local) or Catalyst-compatible |
| Graph | Neo4j Community Edition or AuraDB Free |

---

## 7. Success Criteria (Judging Alignment)

| Judge Priority | Our Answer |
|---------------|-----------|
| "Does it work?" | 5 scenarios execute flawlessly in demo |
| "Is it useful for real police?" | Investigation packages, not chat responses |
| "Is it technically impressive?" | Agent fleet + Neo4j GDS + Prophet + H3 |
| "Is it secure?" | RBAC + audit + jurisdiction scoping |
| "Is it explainable?" | Every output has reasoning trace + citations |
| "Can it scale?" | Pre-computed intelligence pattern scales to 1100 stations |

---

*This document is LOCKED. Changes require explicit version bump and team consensus.*
