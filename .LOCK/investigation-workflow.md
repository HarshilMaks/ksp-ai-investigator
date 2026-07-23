# KSP InvestigateAI — Police Investigation Workflow

## 1. FIR Lifecycle & AI Assistance

### Stage 1: Complaint Reception

**Real-world process:**
- Complainant arrives at police station or calls 112/Hoysala
- Duty officer records initial complaint in General Diary
- Preliminary assessment: cognizable vs non-cognizable

**AI Assistance:**
```
Tool: classifyCrime(complaintText)
→ Returns: Suggested IPC/BNS sections, crime category, severity score
→ Flags: Repeat complainant, known hotspot, similar recent complaints

Tool: extractEntities(complaintText)
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
Tool: suggestSections(crimeDescription, entities)
→ Returns: Primary + secondary sections with confidence scores
→ Cross-references: BNS equivalents, special act applicability

Tool: assignIO(caseComplexity, ioWorkload, ioExpertise)
→ Returns: Recommended IO based on current caseload and specialization

Tool: checkDuplicateFIR(entities, location, timeWindow)
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
Tool: findConnections(entityId, depth=2, relationTypes=[])
→ Returns: Network graph of linked entities across FIRs
→ Highlights: Co-accused, shared assets, communication patterns

Tool: generateLeads(firId)
→ Returns: Prioritized investigation leads based on:
  - Similar MO matches from historical cases
  - Unverified entities needing follow-up
  - Temporal/spatial correlations

Tool: analyzeTimeline(firId)
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
Tool: correlateEvidence(firId, evidenceList)
→ Returns: Evidence strength matrix, gaps in chain of custody
→ Flags: Contradictions, timeline inconsistencies

Tool: analyzeCDR(phoneNumbers[], timeRange)
→ Returns: Communication patterns, tower locations, common contacts

Tool: traceFinancialFlow(accounts[], timeRange)
→ Returns: Money trail visualization, layering detection, mule accounts

Tool: matchMO(moDescriptor)
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
Tool: assessFlightRisk(suspectId)
→ Returns: Risk score based on history, connections, assets

Tool: predictCustodyNeeds(firId, suspectProfile)
→ Returns: Recommended remand duration justification points

Tool: checkAntecedents(personId)
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
Tool: generateChargesheetDraft(firId)
→ Returns: Structured document with all linked evidence and statements
→ Validates: Section applicability, evidence sufficiency per section

Tool: assessCaseStrength(firId)
→ Returns: Prosecution readiness score, evidence gaps, weak links
→ Recommends: Additional investigation needed before filing

Tool: suggestCharges(evidenceSummary, accusedProfile)
→ Returns: Supportable charges with evidence mapping per charge
```

### Stage 7: Trial Support

**Real-world process:**
- Court appearances, witness examination
- Evidence presentation, cross-examination prep
- Verdict and sentencing

**AI Assistance:**
```
Tool: prepareCourtBrief(firId)
→ Returns: Case summary, evidence chronology, witness list with key testimony

Tool: identifyWeaknesses(firId)
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
| 09:00 | Case allocation | `assignIO()` — workload-balanced assignment |
| 10:00 | Review critical cases | `getCaseSummary(firId)` — AI-generated case status |
| 12:00 | Visitor complaints | `classifyCrime()` — quick FIR categorization |
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
| 09:00 | Lead follow-up | `generateLeads(firId)` — next investigation steps |
| 10:00 | Witness recording | `extractEntities()` — auto-extract from statements |
| 12:00 | Evidence analysis | `correlateEvidence()` — link new evidence to case |
| 14:00 | Network exploration | `findConnections()` — discover linked suspects/cases |
| 16:00 | Case documentation | `generateChargesheetDraft()` — progress on filing |
| 18:00 | CDR/financial review | `analyzeCDR()`, `traceFinancialFlow()` |

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
| 10:00 | Hotspot review | `getHotspots(districtCode, timeRange)` — spatial clusters |
| 12:00 | Resource planning | `forecastCrime(districtCode, nextWeek)` — predictive deployment |
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
| 10:00 | Behavioral profiling | `profileOffender(personId)` — behavioral patterns |
| 12:00 | Spatial analysis | `analyzeSpatialPatterns(crimeType, region)` |
| 14:00 | Temporal patterns | `analyzeTemporalPatterns(crimeType)` — time-based trends |
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
| Tue | Policy impact | `correlatePolicyImpact(policy, metrics)` — intervention effectiveness |
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
Tool: detectPatterns(crimeType="Vehicle Theft", region="Bangalore East", timeRange="last90days")
→ Returns: Cluster of 23 cases with similar MO
  - Target: Two-wheelers (Hero Splendor, Honda Activa)
  - Timing: 11 PM - 3 AM
  - Method: Master key, no CCTV coverage areas

Step 2: Network Analysis
Tool: findConnections(entityType="Vehicle", crimeCategory="Vehicle Theft", region="Bangalore East")
→ Returns: Network graph showing:
  - 4 accused persons appearing across 8 FIRs
  - 2 shared phone numbers across accused
  - 1 common vehicle used for transport
  - 3 addresses in same locality (Ramamurthy Nagar)

Step 3: Deep Link Analysis
Tool: expandNetwork(seedNodes=[person1, person2, person3, person4], depth=3)
→ Returns: Extended network:
  - 2 receivers (fence operators) in Kolar district
  - 1 document forger for RC transfers
  - Financial flows to common UPI ID
  - WhatsApp group communication pattern (CDR clustering)

Step 4: Predictive Next Target
Tool: predictNextTarget(networkId, moProfile)
→ Returns:
  - High-risk areas: HSR Layout, Bellandur (expanding geography)
  - High-risk timing: Thursday-Saturday nights
  - Recommended patrol deployment

Step 5: Evidence Package
Tool: generateEvidenceMap(networkId)
→ Returns: Per-accused evidence matrix:
  - Person 1: Present in 5 FIR locations (tower data), shared phone
  - Person 2: Financial flows, vehicle registration links
  - Person 3: CCTV match at 2 locations
  - Person 4: Confiscated master keys, seized vehicles
```

**Outcome:** Single consolidated investigation, all accused charged under IPC 379/411 + Organized Crime

---

### Scenario 2: Cybercrime Repeat Offender

**Trigger:** OTP fraud complaints across multiple PS in Bangalore

**Full Workflow:**

```
Step 1: Complaint Clustering
Tool: clusterComplaints(crimeType="Cybercrime-OTP Fraud", timeRange="last60days")
→ Returns: 15 complaints with similar pattern:
  - Victim receives call claiming to be bank/delivery
  - Victim shares OTP
  - Immediate fund transfer to mule accounts

Step 2: Behavioral Profiling
Tool: profileOffender(indicators={callPattern, scriptAnalysis, targetDemographic})
→ Returns: Offender profile:
  - Operating hours: 10 AM - 6 PM (professional pattern)
  - Target: Senior citizens, recent online shoppers
  - Language: Kannada + Hindi (bilingual script)
  - Technical sophistication: Medium (uses call spoofing)
  - Likely base: Jharkhand/West Bengal (known cybercrime hubs)

Step 3: Financial Trail
Tool: traceFinancialFlow(victimAccounts[], direction="outward", depth=4)
→ Returns: Money layering pattern:
  - Layer 1: Victim → Mule Account A (UPI instant)
  - Layer 2: Mule A → Mule B, C, D (split within 10 min)
  - Layer 3: Mule accounts → Crypto exchange / Gift cards
  - Common mule account controller: Single IMEI operating 6 SIMs

Step 4: IMEI/Phone Analysis
Tool: analyzeIMEI(imeiList, timeRange)
→ Returns:
  - IMEI-1: Used with 6 different SIMs (all prepaid, Jharkhand circles)
  - Tower locations: Concentrated in Deoghar, Jharkhand
  - Call patterns: Bulk calls to Karnataka numbers

Step 5: Cross-State Intelligence
Tool: matchWithNationalDB(offenderProfile, moPattern)
→ Returns:
  - 3 matching FIRs in Maharashtra (same mule accounts)
  - 2 matching FIRs in Tamil Nadu (same IMEI)
  - Known gang operating from Jamtara, Jharkhand
```

**Outcome:** Inter-state coordination request, consolidated chargesheet under IT Act 66C/66D + IPC 420

---

### Scenario 3: Financial Fraud Money Trail

**Trigger:** ₹2.3 Cr investment fraud — multiple victims report same company

**Full Workflow:**

```
Step 1: Entity Extraction
Tool: extractEntities(complaints[])
→ Returns:
  - Company: "GoldenHarvest Investments Pvt Ltd"
  - Directors: 3 persons with PAN/Aadhaar
  - Bank Accounts: 5 company accounts across 3 banks
  - UPI IDs: 4 merchant UPI handles
  - Victims: 47 identified across 8 PS jurisdictions

Step 2: Corporate Network
Tool: analyzeOrganization(companyName, registrationDetails)
→ Returns:
  - Shell company network: 4 related companies (common directors)
  - Registration: 6 months old, inflated authorized capital
  - Office address: Virtual office, no physical presence
  - Similar companies flagged by SEBI

Step 3: Full Financial Flow
Tool: traceFinancialFlow(companyAccounts[], timeRange="12months", detail="full")
→ Returns: Complete money map:
  - Inflows: ₹4.7 Cr from 120+ individuals
  - Outflows:
    - ₹1.2 Cr → Director personal accounts
    - ₹0.8 Cr → Real estate (benami property suspected)
    - ₹0.5 Cr → Crypto exchanges
    - ₹1.1 Cr → Sister companies (round-tripping)
    - ₹0.3 Cr → Cash withdrawals (ATM clusters)

Step 4: Asset Tracing
Tool: traceAssets(directorIds[])
→ Returns:
  - 3 properties registered in family names (last 6 months)
  - 2 luxury vehicles purchased
  - Gold purchases via linked credit cards
  - Foreign remittances to Dubai

Step 5: Victim Impact & Case Building
Tool: assessCaseStrength(firId, charges=["IPC 420", "IPC 406", "KPID Act"])
→ Returns:
  - Evidence strength: Strong (documentary + digital)
  - Recommended charges: IPC 420, 406, 120B + KPID Act + PMLA
  - Attachment recommendations: Properties, vehicles, bank balances
  - Estimated recoverable assets: ₹2.1 Cr
```

**Outcome:** Multi-jurisdictional FIR, ED/EOW referral, property attachment under PMLA

---

### Scenario 4: Chain Snatching Forecast

**Trigger:** Proactive analysis — seasonal pattern detection

**Full Workflow:**

```
Step 1: Historical Pattern Analysis
Tool: analyzeTemporalPatterns(crimeType="Chain Snatching", region="Bangalore", years=3)
→ Returns:
  - Peak months: October-January (festival season)
  - Peak days: Tuesday, Friday (temple/market days)
  - Peak hours: 6-8 AM (morning walkers), 6-9 PM (evening)
  - Year-over-year: 15% increase trend

Step 2: Spatial Hotspot Mapping
Tool: getHotspots(crimeType="Chain Snatching", granularity="500m", minIncidents=3)
→ Returns: Top 20 hotspots:
  - Jayanagar 4th Block market area
  - Malleshwaram 8th Cross
  - Basavanagudi Bull Temple Road
  - Commercial Street periphery
  - [Ranked by incident density and recency]

Step 3: Predictive Forecast
Tool: forecastCrime(crimeType="Chain Snatching", region="Bangalore", horizon="next30days")
→ Returns:
  - Predicted incidents: 45-55 (confidence: 78%)
  - High-risk zones: 8 areas with >70% probability
  - Risk multipliers: Upcoming Dasara festival (+40%), gold price rise (+15%)
  - Recommended patrol: Map with time-slot-specific deployment

Step 4: Offender Pattern
Tool: profileRecentOffenders(crimeType="Chain Snatching", timeRange="last6months")
→ Returns:
  - Typical profile: Male, 18-28, two-wheeler, operates in pairs
  - Common MO: Approach from behind on bike, snatch, flee via known routes
  - Escape routes: Mapped common flee directions per hotspot
  - Recidivism: 35% of caught offenders are repeat

Step 5: Deployment Recommendation
Tool: generateDeploymentPlan(forecast, availableResources)
→ Returns:
  - Patrol schedule: Time-slot × location matrix
  - Plainclothes deployment: High-value target areas
  - CCTV gap analysis: Blind spots on escape routes
  - Decoy operation suggestions: Based on offender targeting pattern
```

**Outcome:** Preventive deployment, 30% reduction in incidents during festival season

---

### Scenario 5: Hypothesis Investigation

**Trigger:** IO hypothesis: "Multiple burglaries in JP Nagar are by same gang"

**Full Workflow:**

```
Step 1: Hypothesis Formulation
Tool: formulateHypothesis(
  claim="JP Nagar burglaries (last 3 months) are connected",
  supportingFIRs=[FIR-1, FIR-2, FIR-3, FIR-4, FIR-5, FIR-6],
  criteria=["same_MO", "temporal_proximity", "geographic_cluster"]
)
→ Returns: Structured hypothesis with testable predictions

Step 2: Evidence Evaluation (For)
Tool: evaluateEvidence(hypothesis, direction="supporting")
→ Returns:
  - MO similarity score: 0.82 (high) — all use glass cutter, target ground floor
  - Temporal pattern: All between 2-5 AM, all on weeknights
  - Geographic: All within 2 km radius
  - Tool marks: Forensic report matches on 3/6 cases
  - Supporting strength: MODERATE-HIGH

Step 3: Evidence Evaluation (Against)
Tool: evaluateEvidence(hypothesis, direction="contradicting")
→ Returns:
  - FIR-4: Different entry method (door pry vs glass cut)
  - FIR-6: Timing anomaly (Saturday night vs weeknight pattern)
  - No common fingerprints across scenes
  - Contradicting strength: LOW-MODERATE

Step 4: Alternative Hypotheses
Tool: generateAlternatives(hypothesis)
→ Returns:
  - Alt-1: Two separate pairs copying same MO (confidence: 25%)
  - Alt-2: Single gang but FIR-4, FIR-6 are unrelated (confidence: 40%)
  - Alt-3: Original hypothesis correct for all 6 (confidence: 35%)

Step 5: Investigation Recommendations
Tool: recommendNextSteps(hypothesis, evidenceState)
→ Returns:
  - Priority 1: Compare CCTV from adjacent roads for FIR-1,2,3,5 (likely same vehicle)
  - Priority 2: CDR analysis of tower data near crime scenes at crime times
  - Priority 3: Check pawnshops/receivers for stolen items from multiple FIRs
  - Priority 4: Re-examine FIR-4,6 separately — may be copycat
  - Estimated effort: 3-4 days to confirm/reject hypothesis
```

**Outcome:** Hypothesis partially confirmed (4/6 FIRs connected), leads to gang identification

---

## 4. AI Interaction Patterns

### Natural Language Queries (Examples)

| User Query | AI Interpretation | Tool Chain |
|------------|-------------------|------------|
| "Show me all cases linked to this phone number" | Entity lookup + connection traversal | `findEntity()` → `findConnections()` |
| "Is this accused involved in other cases?" | Person-FIR relationship search | `checkAntecedents()` |
| "What's the crime trend in Koramangala?" | Spatial-temporal analysis | `analyzeTemporalPatterns()` + `getHotspots()` |
| "Find similar MO cases" | Modus operandi matching | `matchMO()` |
| "Who else uses this vehicle?" | Entity relationship traversal | `findConnections(entityType="Vehicle")` |
| "Generate leads for this case" | Multi-factor lead generation | `generateLeads()` |
| "Is this case strong enough for chargesheet?" | Evidence sufficiency analysis | `assessCaseStrength()` |

### Confidence & Transparency

All AI outputs include:
- **Confidence score** (0-1) for each finding
- **Evidence basis** — which FIRs/entities support the conclusion
- **Limitations** — what data was unavailable or incomplete
- **Recommended verification** — human steps to confirm AI findings
