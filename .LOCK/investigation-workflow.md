# KSP InvestigateAI — Police Investigation Workflow
> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24


## Tool registry boundary

Workflow labels below are mapped to the internal typed T01-T23 registry from AGENTS.md. They are not additional public APIs. Where no canonical tool exists, the item is explicitly marked **future capability** and remains human-reviewed.

The scenarios below are illustrative design outputs using synthetic/example data; they are support-review aids, not achieved accuracy, legal, custody, charging, or asset-recovery claims.

## Engine and reasoning-stage mapping

| Workflow need | Deterministic engine | Reasoning stage (only when needed) |
|---|---|---|
| Structured FIR lookup, counts, filters | SQL Retrieval | None on fast path |
| Similar/semantic cases and ranking | Search/Ranking | Planner only if intent is ambiguous |
| Associations, paths, communities | Graph Intelligence | Reasoner for grounded synthesis |
| MO/anomaly/temporal pattern | Pattern Analysis | Reasoner for hypothesis evaluation |
| Offender/profile signals | Behavioral Profiling | Reporter for wording if requested |
| Account trails and flow flags | Financial Analysis | Reasoner for contradiction-aware synthesis |
| Hotspots and future signals | Forecasting | Reporter for briefing language |
| Chronology and gaps | Timeline | Reporter for package wording |
| Citations, numbers, permissions, contradictions | Evidence/Explainability | Gate before every response |

Decision Support is the deterministic Lead Ranking Engine; optional LLM explanation occurs only after the evidence gate. Planner, Reasoner, and Reporter are not invoked for work a deterministic engine can complete.

## 1. FIR Lifecycle & AI Assistance

### Stage 1: Complaint Reception

**Real-world process:**
- Complainant arrives at police station or calls 112/Hoysala
- Duty officer records initial complaint in General Diary
- Preliminary assessment: cognizable vs non-cognizable

**AI Assistance:**
```
Tool: T16 case_summarize (Search/Ranking or SQL Retrieval engine) (classification step)(complaintText)
→ Returns: Suggested IPC/BNS sections, crime category, severity score
→ Flags: Repeat complainant, known hotspot, similar recent complaints

Tool: T07 entity_resolve (extraction is an internal pipeline step)(complaintText)
→ Returns: Persons, vehicles, locations, phone numbers, timestamps
→ Auto-populates FIR draft fields
```

### Stage 2: FIR Registration

**Real-world process:**
- FIR registered in CCTNS with unique number (State/District/PS/Year/Serial)
- Sections of law applied (IPC/BNS + Special Acts)
- IO assigned by SHO
- Zero FIR provision if jurisdiction differs

**AI Assistance:**
```
Tool: future capability: legal-section suggestion for human review(crimeDescription, entities)
→ Returns: Primary + secondary sections with confidence scores
→ Cross-references: BNS equivalents, special act applicability

Tool: future capability: workload-aware IO assignment(caseComplexity, ioWorkload, ioExpertise)
→ Returns: Recommended IO based on current caseload and specialization

Tool: T01 sql_query + T13 similar_cases(entities, location, timeWindow)
→ Returns: Potential duplicate/related FIRs within jurisdiction
```

### Stage 3: Investigation

**Real-world process:**
- IO visits crime scene, records panchnama
- Witness statements (161 CrPC)
- Technical evidence requests (CDR, CCTV, bank records)
- Suspect identification and tracking

**AI Assistance:**
```
Tool: T03 graph_traverse (Graph Intelligence engine)(entityId, depth=2, relationTypes=[])
→ Returns: Network graph of linked entities across FIRs
→ Highlights: Co-accused, shared assets, communication patterns

Tool: T15 lead_generate (deterministic Lead Ranking Engine)(firId)
→ Returns: Prioritized investigation leads based on:
  - Similar MO matches from historical cases
  - Unverified entities needing follow-up
  - Temporal/spatial correlations

Tool: T14 timeline_build (Timeline engine)(firId)
→ Returns: Chronological event reconstruction with gaps identified
```

### Stage 4: Evidence Collection

**Real-world process:**
- Digital evidence: CDR analysis, IP logs, social media
- Physical evidence: forensics, fingerprints, DNA
- Documentary evidence: bank statements, property records
- Electronic evidence: CCTV footage, GPS data

**AI Assistance:**
```
Tool: T20 explain_reasoning (Evidence/Explainability engine; Reasoner only for synthesis)(firId, evidenceList)
→ Returns: Evidence strength matrix, gaps in chain of custody
→ Flags: Contradictions, timeline inconsistencies

Tool: T03 graph_traverse (Graph Intelligence engine) (phone relationships)(phoneNumbers[], timeRange)
→ Returns: Communication patterns, tower locations, common contacts

Tool: T11 financial_trail (Financial Analysis engine)(accounts[], timeRange)
→ Returns: Money trail visualization, layering detection, mule accounts

Tool: T08 pattern_match (Pattern Analysis engine)(moDescriptor)
→ Returns: Historical cases with similar modus operandi, ranked by similarity
```

### Stage 5: Arrest

**Real-world process:**
- Arrest under warrant or cognizable offence provisions
- Arrest memo, medical examination
- Production before magistrate within 24 hours
- Remand application if needed

**AI Assistance:**
```
Tool: T12 offender_profile (Behavioral Profiling engine) (review signal)(suspectId)
→ Returns: Risk score based on history, connections, assets

Tool: future capability: custody planning support(firId, suspectProfile)
→ Returns: Review points for an authorized custody decision

Tool: T12 offender_profile (Behavioral Profiling engine)(personId)
→ Returns: Prior cases, conviction history, pending warrants, bail jumps
```

### Stage 6: Chargesheet

**Real-world process:**
- Filed within 60/90 days (depending on offence severity)
- Contains: FIR, statements, evidence list, accused details
- Supplementary chargesheet for additional evidence
- Final report if case unfounded

**AI Assistance:**
```
Tool: T21 generate_report (Reporter stage over evidence-gated results) (draft support; human review)(firId)
→ Returns: Structured document with all linked evidence and statements
→ Validates: Section applicability, evidence sufficiency per section

Tool: T20 explain_reasoning (Evidence/Explainability engine; Reasoner only for synthesis) (review support)(firId)
→ Returns: Prosecution readiness score, evidence gaps, weak links
→ Recommends: Additional investigation needed before filing

Tool: future capability: charge review support(evidenceSummary, accusedProfile)
→ Returns: Supportable charges with evidence mapping per charge
```

### Stage 7: Trial Support

**Real-world process:**
- Court appearances, witness examination
- Evidence presentation, cross-examination prep
- Verdict and sentencing

**AI Assistance:**
```
Tool: T21 generate_report (Reporter stage over evidence-gated results) (audit-oriented brief; not a legal determination)(firId)
→ Returns: Case summary, evidence chronology, witness list with key testimony

Tool: T15 lead_generate (deterministic Lead Ranking Engine) (evidence-gap leads)(firId)
→ Returns: Potential defense arguments, evidence vulnerabilities
```

---

## 2. User Personas & Daily Workflows

### SHO (Station House Officer)

**Role:** Oversees entire police station operations, 50-200 active cases

**Daily Workflow:**
| Time | Activity | AI Tool |
|------|----------|---------|
| 08:00 | Morning briefing | `getStationDashboard(psCode)` — overnight incidents, pending tasks |
| 09:00 | Case allocation | `future capability: workload-aware IO assignment()` — workload-balanced assignment |
| 10:00 | Review critical cases | `getCaseSummary(firId)` — AI-generated case status |
| 12:00 | Visitor complaints | `T16 case_summarize (Search/Ranking or SQL Retrieval engine) (classification step)()` — quick FIR categorization |
| 14:00 | Supervision | `getIOProgress(ioId)` — investigation milestones |
| 16:00 | Reporting | `generateStationReport()` — daily/weekly crime stats |
| 18:00 | Alerts review | `getAlerts(psCode)` — chargesheet deadlines, court dates |

**Key Needs:**
- Real-time station dashboard with case counts by status
- Deadline alerts (chargesheet filing, court dates, remand expiry)
- Quick case summaries without reading full case files
- Crime pattern alerts for jurisdiction

---

### IO (Investigating Officer)

**Role:** Actively investigates assigned cases (typically 20-40 simultaneously)

**Daily Workflow:**
| Time | Activity | AI Tool |
|------|----------|---------|
| 08:00 | Case priorities | `getInvestigationQueue(ioId)` — deadline-sorted task list |
| 09:00 | Lead follow-up | `T15 lead_generate (deterministic Lead Ranking Engine)(firId)` — next investigation steps |
| 10:00 | Witness recording | `T07 entity_resolve (extraction is an internal pipeline step)()` — auto-extract from statements |
| 12:00 | Evidence analysis | `T20 explain_reasoning (Evidence/Explainability engine; Reasoner only for synthesis)()` — link new evidence to case |
| 14:00 | Network exploration | `T03 graph_traverse (Graph Intelligence engine)()` — discover linked suspects/cases |
| 16:00 | Case documentation | `T21 generate_report (Reporter stage over evidence-gated results) (draft support; human review)()` — progress on filing |
| 18:00 | CDR/financial review | `T03 graph_traverse (Graph Intelligence engine) (phone relationships)()`, `T11 financial_trail (Financial Analysis engine)()` |

**Key Needs:**
- Lead generation: "What should I investigate next?"
- Connection discovery: "Who else is linked to this suspect?"
- Evidence mapping: "Do I have enough to charge under Section X?"
- Historical pattern matching: "Has this MO appeared before?"

---

### DCP (Deputy Commissioner of Police)

**Role:** District-level supervision, resource allocation, crime trends

**Daily Workflow:**
| Time | Activity | AI Tool |
|------|----------|---------|
| 08:00 | District overview | `getDistrictDashboard(districtCode)` — crime stats, trends |
| 10:00 | Hotspot review | `T10 hotspot_detect (Forecasting/Pattern Analysis engine)(districtCode, timeRange)` — spatial clusters |
| 12:00 | Resource planning | `T17 forecast_crime (Forecasting engine) (aggregate risk signal)(districtCode, nextWeek)` — predictive deployment |
| 14:00 | Sensitive cases | `getCaseSummary()` — high-profile case tracking |
| 16:00 | Inter-station links | `findCrossJurisdictionLinks()` — connected cases across PS |

**Key Needs:**
- Crime trend visualization (week-over-week, seasonal)
- Hotspot maps for patrol deployment
- Cross-station case connections
- Performance metrics per station/IO
- Early warning on emerging crime patterns

---

### Analyst (Crime Analysis Unit)

**Role:** Deep analysis, pattern detection, intelligence generation

**Daily Workflow:**
| Time | Activity | AI Tool |
|------|----------|---------|
| 08:00 | Network monitoring | `detectNetworks(criteria)` — new criminal networks |
| 10:00 | Behavioral profiling | `T12 offender_profile (Behavioral Profiling engine)(personId)` — behavioral patterns |
| 12:00 | Spatial analysis | `analyzeSpatialPatterns(crimeType, region)` |
| 14:00 | Temporal patterns | `T09 temporal_analysis(crimeType)` — time-based trends |
| 16:00 | Report generation | `generateIntelligenceReport()` — actionable intelligence |

**Key Needs:**
- Network detection and visualization
- Offender behavioral profiling
- Spatial-temporal pattern analysis
- Anomaly detection in crime data
- Link analysis across large datasets

---

### SP (Superintendent of Police)

**Role:** Strategic oversight, policy decisions, inter-district coordination

**Weekly Workflow:**
| Day | Activity | AI Tool |
|-----|----------|---------|
| Mon | Weekly crime review | `getRegionalTrends()` — multi-district comparison |
| Tue | Policy impact | `T18 demographic_correlate + T09 temporal_analysis(policy, metrics)` — intervention effectiveness |
| Wed | Resource strategy | `forecastResourceNeeds()` — manpower/equipment planning |
| Thu | Inter-agency intel | `crossReferenceNationalDB()` — NCRB, interstate links |
| Fri | Sociological trends | `analyzeSociologicalFactors()` — demographics, economic correlation |

**Key Needs:**
- Macro-level crime trends and forecasting
- Policy effectiveness measurement
- Sociological factor correlation
- Inter-district and interstate crime links
- Strategic resource allocation recommendations

---

## 3. Investigation Scenarios (Demo Workflows)

### Scenario 1: Organized Vehicle Theft Ring

**Trigger:** Multiple vehicle theft FIRs in Whitefield, Marathahalli, KR Puram (East Bangalore)

**Full Workflow:**

```
Step 1: Pattern Detection
Tool: T08 pattern_match (Pattern Analysis engine)(crimeType="Vehicle Theft", region="Bangalore East", timeRange="last90days")
→ Returns: Cluster of 23 cases with similar MO
  - Target: Two-wheelers (Hero Splendor, Honda Activa)
  - Timing: 11 PM - 3 AM
  - Method: Master key, no CCTV coverage areas

Step 2: Network Analysis
Tool: T03 graph_traverse (Graph Intelligence engine)(entityType="Vehicle", crimeCategory="Vehicle Theft", region="Bangalore East")
→ Returns: Network graph showing:
  - 4 accused persons appearing across 8 FIRs
  - 2 shared phone numbers across accused
  - 1 common vehicle used for transport
  - 3 addresses in same locality (Ramamurthy Nagar)

Step 3: Deep Link Analysis
Tool: T03 graph_traverse (Graph Intelligence engine)(seedNodes=[person1, person2, person3, person4], depth=3)
→ Returns: Extended network:
  - 2 receivers (fence operators) in Kolar district
  - 1 document forger for RC transfers
  - Financial flows to common UPI ID
  - WhatsApp group communication pattern (CDR clustering)

Step 4: Predictive Next Target
Tool: T17 forecast_crime (Forecasting engine) (risk signal, not a prediction of a person)(networkId, moProfile)
→ Returns:
  - High-risk areas: HSR Layout, Bellandur (expanding geography)
  - High-risk timing: Thursday-Saturday nights
  - Recommended patrol deployment

Step 5: Evidence Package
Tool: T22 pin_evidence(networkId)
→ Returns: Per-accused evidence matrix:
  - Person 1: Present in 5 FIR locations (tower data), shared phone
  - Person 2: Financial flows, vehicle registration links
  - Person 3: CCTV match at 2 locations
  - Person 4: Confiscated master keys, seized vehicles
```

**Support-review output:** Single consolidated investigation, possible linkages and relevant sections presented for authorized human review

---

### Scenario 2: Cybercrime Repeat Offender

**Trigger:** OTP fraud complaints across multiple PS in Bangalore

**Full Workflow:**

```
Step 1: Complaint Clustering
Tool: T08 pattern_match (Pattern Analysis engine)(crimeType="Cybercrime-OTP Fraud", timeRange="last60days")
→ Returns: 15 complaints with similar pattern:
  - Victim receives call claiming to be bank/delivery
  - Victim shares OTP
  - Immediate fund transfer to mule accounts

Step 2: Behavioral Profiling
Tool: T12 offender_profile (Behavioral Profiling engine)(indicators={callPattern, scriptAnalysis, targetDemographic})
→ Returns: Offender profile:
  - Operating hours: 10 AM - 6 PM (professional pattern)
  - Target: Senior citizens, recent online shoppers
  - Language: Kannada + Hindi (bilingual script)
  - Technical sophistication: Medium (uses call spoofing)
  - Likely base: Jharkhand/West Bengal (known cybercrime hubs)

Step 3: Financial Trail
Tool: T11 financial_trail (Financial Analysis engine)(victimAccounts[], direction="outward", depth=4)
→ Returns: Money layering pattern:
  - Layer 1: Victim → Mule Account A (UPI instant)
  - Layer 2: Mule A → Mule B, C, D (split within 10 min)
  - Layer 3: Mule accounts → Crypto exchange / Gift cards
  - Common mule account controller: Single IMEI operating 6 SIMs

Step 4: IMEI/Phone Analysis
Tool: T03 graph_traverse (Graph Intelligence engine)(imeiList, timeRange)
→ Returns:
  - IMEI-1: Used with 6 different SIMs (all prepaid, Jharkhand circles)
  - Tower locations: Concentrated in Deoghar, Jharkhand
  - Call patterns: Bulk calls to Karnataka numbers

Step 5: Cross-State Intelligence
Tool: future capability: external database integration(offenderProfile, moPattern)
→ Returns:
  - 3 matching FIRs in Maharashtra (same mule accounts)
  - 2 matching FIRs in Tamil Nadu (same IMEI)
  - Known gang operating from Jamtara, Jharkhand
```

**Support-review output:** Inter-state coordination request, coordination and report inputs for authorized human review

---

### Scenario 3: Financial Fraud Money Trail

**Trigger:** ₹2.3 Cr investment fraud — multiple victims report same company

**Full Workflow:**

```
Step 1: Entity Extraction
Tool: T07 entity_resolve (extraction is an internal pipeline step)(complaints[])
→ Returns:
  - Company: "GoldenHarvest Investments Pvt Ltd"
  - Directors: 3 persons with PAN/Aadhaar
  - Bank Accounts: 5 company accounts across 3 banks
  - UPI IDs: 4 merchant UPI handles
  - Victims: 47 identified across 8 PS jurisdictions

Step 2: Corporate Network
Tool: future capability: organization enrichment(companyName, registrationDetails)
→ Returns:
  - Shell company network: 4 related companies (common directors)
  - Registration: 6 months old, inflated authorized capital
  - Office address: Virtual office, no physical presence
  - Similar companies flagged by SEBI

Step 3: Full Financial Flow
Tool: T11 financial_trail (Financial Analysis engine)(companyAccounts[], timeRange="12months", detail="full")
→ Returns: Complete money map:
  - Inflows: ₹4.7 Cr from 120+ individuals
  - Outflows:
    - ₹1.2 Cr → Director personal accounts
    - ₹0.8 Cr → Real estate (benami property suspected)
    - ₹0.5 Cr → Crypto exchanges
    - ₹1.1 Cr → Sister companies (round-tripping)
    - ₹0.3 Cr → Cash withdrawals (ATM clusters)

Step 4: Asset Tracing
Tool: T11 financial_trail (Financial Analysis engine) (asset/financial review)(directorIds[])
→ Returns:
  - 3 properties registered in family names (last 6 months)
  - 2 luxury vehicles purchased
  - Gold purchases via linked credit cards
  - Foreign remittances to Dubai

Step 5: Victim Impact & Case Building
Tool: T20 explain_reasoning (Evidence/Explainability engine; Reasoner only for synthesis) (review support)(firId, charges=["IPC 420", "IPC 406", "KPID Act"])
→ Returns:
  - Evidence strength: Strong (documentary + digital)
  - Potential sections for authorized human review (not a charging decision): IPC 420, 406, 120B + KPID Act + PMLA
  - Asset-review candidates: properties, vehicles, bank balances
  - Candidate asset estimate for review: ₹2.1 Cr (not a verified recovery claim)
```

**Support-review output:** review package for possible multi-jurisdictional coordination and referrals; legal actions remain with authorized officers

---

### Scenario 4: Chain Snatching Forecast

**Trigger:** Proactive analysis — seasonal pattern detection

**Full Workflow:**

```
Step 1: Historical Pattern Analysis
Tool: T09 temporal_analysis(crimeType="Chain Snatching", region="Bangalore", years=3)
→ Returns:
  - Peak months: October-January (festival season)
  - Peak days: Tuesday, Friday (temple/market days)
  - Peak hours: 6-8 AM (morning walkers), 6-9 PM (evening)
  - Illustrative trend; percentage requires benchmark validation

Step 2: Spatial Hotspot Mapping
Tool: T10 hotspot_detect (Forecasting/Pattern Analysis engine)(crimeType="Chain Snatching", granularity="500m", minIncidents=3)
→ Returns: Top 20 hotspots:
  - Jayanagar 4th Block market area
  - Malleshwaram 8th Cross
  - Basavanagudi Bull Temple Road
  - Commercial Street periphery
  - [Ranked by incident density and recency]

Step 3: Predictive Forecast
Tool: T17 forecast_crime (Forecasting engine) (aggregate risk signal)(crimeType="Chain Snatching", region="Bangalore", horizon="next30days")
→ Returns:
  - Illustrative aggregate forecast range; confidence requires benchmark validation
  - High-risk zones: aggregate risk signal; probability requires benchmark validation
  - Risk multipliers: Upcoming Dasara festival (+40%), gold price rise (+15%)
  - Recommended patrol: Map with time-slot-specific deployment

Step 4: Offender Pattern
Tool: T12 offender_profile (Behavioral Profiling engine)(crimeType="Chain Snatching", timeRange="last6months")
→ Returns:
  - Typical profile: Male, 18-28, two-wheeler, operates in pairs
  - Common MO: Approach from behind on bike, snatch, flee via known routes
  - Escape routes: Mapped common flee directions per hotspot
  - Repeat-offender indicator; percentage requires benchmark validation

Step 5: Deployment Recommendation
Tool: future capability: deployment planning support(forecast, availableResources)
→ Returns:
  - Patrol schedule: Time-slot × location matrix
  - Plainclothes deployment: High-value target areas
  - CCTV gap analysis: Blind spots on escape routes
  - Decoy operation suggestions: Based on offender targeting pattern
```

**Support-review output:** Preventive deployment, possible preventive deployment signal; impact percentage requires dated benchmark

---

### Scenario 5: Hypothesis Investigation

**Trigger:** IO hypothesis: "Multiple burglaries in JP Nagar are by same gang"

**Full Workflow:**

```
Step 1: Hypothesis Formulation
Tool: T15 lead_generate (deterministic Lead Ranking Engine) (hypothesis lead)(
  claim="JP Nagar burglaries (last 3 months) are connected",
  supportingFIRs=[FIR-1, FIR-2, FIR-3, FIR-4, FIR-5, FIR-6],
  criteria=["same_MO", "temporal_proximity", "geographic_cluster"]
)
→ Returns: Structured hypothesis with testable predictions

Step 2: Evidence Evaluation (For)
Tool: T20 explain_reasoning (Evidence/Explainability engine; Reasoner only for synthesis)(hypothesis, direction="supporting")
→ Returns:
  - MO similarity score: 0.82 (high) — all use glass cutter, target ground floor
  - Temporal pattern: All between 2-5 AM, all on weeknights
  - Geographic: All within 2 km radius
  - Tool marks: Forensic report matches on 3/6 cases
  - Supporting strength: MODERATE-HIGH

Step 3: Evidence Evaluation (Against)
Tool: T20 explain_reasoning (Evidence/Explainability engine; Reasoner only for synthesis)(hypothesis, direction="contradicting")
→ Returns:
  - FIR-4: Different entry method (door pry vs glass cut)
  - FIR-6: Timing anomaly (Saturday night vs weeknight pattern)
  - No common fingerprints across scenes
  - Contradicting strength: LOW-MODERATE

Step 4: Alternative Hypotheses
Tool: T15 lead_generate (deterministic Lead Ranking Engine)(hypothesis)
→ Returns:
  - Alt-1: Two separate pairs copying same MO (confidence: 25%)
  - Alt-2: Single gang but FIR-4, FIR-6 are unrelated (confidence: 40%)
  - Alt-3: Original hypothesis correct for all 6 (confidence: 35%)

Step 5: Investigation Recommendations
Tool: T15 lead_generate (deterministic Lead Ranking Engine)(hypothesis, evidenceState)
→ Returns:
  - Priority 1: Compare CCTV from adjacent roads for FIR-1,2,3,5 (likely same vehicle)
  - Priority 2: CDR analysis of tower data near crime scenes at crime times
  - Priority 3: Check pawnshops/receivers for stolen items from multiple FIRs
  - Priority 4: Re-examine FIR-4,6 separately — may be copycat
  - Estimated effort: 3-4 days to confirm/reject hypothesis
```

**Support-review output:** hypothesis evidence state and leads presented for human review; connection counts require measured validation

---

## 4. AI Interaction Patterns

### Natural Language Queries (Examples)

| User Query | AI Interpretation | Tool Chain |
|------------|-------------------|------------|
| "Show me all cases linked to this phone number" | Entity lookup + connection traversal | `findEntity()` → `T03 graph_traverse (Graph Intelligence engine)()` |
| "Is this accused involved in other cases?" | Person-FIR relationship search | `T12 offender_profile (Behavioral Profiling engine)()` |
| "What's the crime trend in Koramangala?" | Spatial-temporal analysis | `T09 temporal_analysis()` + `T10 hotspot_detect (Forecasting/Pattern Analysis engine)()` |
| "Find similar MO cases" | Modus operandi matching | `T08 pattern_match (Pattern Analysis engine)()` |
| "Who else uses this vehicle?" | Entity relationship traversal | `T03 graph_traverse (Graph Intelligence engine)(entityType="Vehicle")` |
| "Generate leads for this case" | Multi-factor lead generation | `T15 lead_generate (deterministic Lead Ranking Engine)()` |
| "Is this case strong enough for chargesheet?" | Evidence sufficiency analysis | `T20 explain_reasoning (Evidence/Explainability engine; Reasoner only for synthesis) (review support)()` |

### Confidence & Transparency

All AI outputs include:
- **Confidence score** (0-1) for each finding
- **Evidence basis** — which FIRs/entities support the conclusion
- **Limitations** — what data was unavailable or incomplete
- **Recommended verification** — human steps to confirm AI findings
