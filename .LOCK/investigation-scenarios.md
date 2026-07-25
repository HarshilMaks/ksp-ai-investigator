# Investigation Scenarios — Demo Scripts & Integration Tests
> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24

---

> These 10 scenarios serve triple duty: **demo scripts** for judges, **integration tests** for CI, and **proof** that the architecture satisfies all 10 Challenge 1 requirements. Each uses synthetic data with realistic Bangalore geography, Kannada names, IPC/BNS sections, and plausible amounts.

---

## Scenario 1: Organized Vehicle Theft Ring

### Title and Crime Type
**Organized Vehicle Theft Ring** — IPC 379/BNS 303 (Theft), IPC 413/BNS 317 (Habitually dealing in stolen property), IPC 120B/BNS 61 (Criminal Conspiracy)

### Officer Persona
**IO (Investigating Officer)** — SI Kavitha R., Whitefield PS, assigned FIR WF-2026-0341

### Investigation Goal
Identify all members of a suspected interstate vehicle theft gang operating across Whitefield, KR Puram, and Mahadevapura; link them through shared phone IMEIs and stolen vehicles appearing in multiple FIRs.

### Opening Query
> "Show me all vehicle theft FIRs in Whitefield and KR Puram from the last 6 months where stolen vehicles or suspect phone numbers appear in more than one case"

### Route Taken
**Deep path** — ambiguous multi-entity cross-case query requiring parallel engine execution.

### Engines Invoked
1. **SQL Retrieval Engine** — Filter FIRs by IPC 379, jurisdiction (Whitefield, KR Puram, Mahadevapura), date range (Jan–Jun 2026)
2. **Graph Intelligence Engine** — Expand shared IMEI nodes and vehicle registration nodes; detect community clusters via Louvain
3. **Pattern Analysis Engine** — Identify temporal MO patterns (time-of-day, day-of-week, target vehicle types)
4. **Behavioral Profiling Engine** — Build gang profile from linked accused
5. **Search/Ranking Engine** — Retrieve similar historical cases from 2024-2025 for known gangs

### Evidence Surfaced
| Item | Details |
|------|---------|
| FIRs Linked | WF-2026-0341, WF-2026-0298, WF-2026-0187, KRP-2026-0112, KRP-2026-0089, KRP-2026-0045, MDP-2026-0201, MDP-2026-0156, MDP-2026-0134, MDP-2026-0099, WF-2025-0891, KRP-2025-0445 |
| Shared IMEI | IMEI 3548920XXXXXXX appears in 4 FIRs (phones swapped between Suresh M. and Venkatesh G.) |
| Shared Vehicle | KA-01-MH-4521 (Maruti Eeco, used as transport) found in 3 FIR witness statements |
| Gang Members | 7 identified: Ravi Gowda (leader, Hosur), Suresh M. (spotter), Venkatesh G. (driver), Nagaraj T. (key-maker), Prakash D. (buyer-Hosur), Manjunath S. (buyer-Chennai), Deepak R. (logistics) |
| Interstate Link | Vehicles traced to Hosur (TN) and Chennai resale markets via transport receipts |

### Intelligence Cards Generated
- **Network Card** — 7-node gang structure with role labels and PageRank centrality (Ravi Gowda: 0.34)
- **Entity Profile Card** — Ravi Gowda: 4 priors, escalation from petty theft to organized ring
- **Pattern Card** — MO signature: targets parked two-wheelers 11 PM–3 AM, Tue/Thu/Sat
- **Similar Cases Card** — 2024 Rajajinagar gang (dismantled) had identical MO

### Artifacts Produced
- **Relationship Graph** — Cytoscape.js interactive 7-node + 12-FIR bipartite graph
- **Timeline** — 6-month event timeline showing escalation from 1 theft/month to 3/month
- **Ranked Leads** — (1) Arrest Ravi Gowda at Hosur address, (2) Surveil Maruti Eeco KA-01-MH-4521, (3) Request TN police cooperation for Chennai buyer
- **Investigation Package PDF** — Exportable brief with network diagram, evidence list, lead priorities

### Proactive Alert
> 🔴 **ALERT:** New FIR MDP-2026-0267 filed 2 hours ago — stolen Honda Activa from Marathahalli. Witness describes white Maruti Eeco (partial plate KA-01-MH-45XX). IMEI 3548920XXXXXXX detected in CDR near crime scene. **Matches your active investigation.**

### Hypothesis Tested
**H1: "Are the Whitefield and KR Puram thefts committed by the same gang?"**
- Supporting evidence strength: 0.87 — shared IMEIs (4 FIRs), shared vehicle (3 FIRs), overlapping accused names (5 FIRs), consistent MO
- Contradicting evidence: 0.12 — 2 FIRs have dissimilar timing (daytime), possibly copycat
- Verdict: **Strongly Supported**
- Missing: CDR tower triangulation for 2 unconfirmed members

### Demo Talking Point
> "The officer typed ONE natural language question. The system automatically discovered a 7-member interstate gang by linking 12 FIRs through shared phone IMEIs and vehicles — connections that would take weeks of manual cross-referencing. Every claim is cited to a specific FIR."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 1: Conversational Intelligence | Natural language query triggers full investigation |
| Req 2: Criminal Network Analysis | Louvain community detection, PageRank centrality, interactive graph |
| Req 3: Crime Pattern Analysis | Temporal MO pattern (time/day clustering) |
| Req 5: Offender Profiling | Gang member profiles with escalation history |
| Req 6: Decision Support | Ranked leads with confidence scores |
| Req 9: Explainable AI | Every link cited to specific FIR + evidence type |

---

## Scenario 2: Cybercrime Repeat Offender

### Title and Crime Type
**Cybercrime Repeat Offender Profiling** — IT Act 66C (Identity Theft), 66D (Cheating by Personation using Computer Resource), IPC 420/BNS 318 (Cheating), IPC 468/BNS 336 (Forgery for Cheating)

### Officer Persona
**Analyst** — Crime Analyst Priya Sharma, Cybercrime Division, Bangalore City

### Investigation Goal
Profile a habitual cybercriminal showing clear escalation from phishing individuals to corporate fraud; predict next likely target type and recommend preventive action.

### Opening Query
> "Profile the offender 'Arjun Reddy' from cybercrime cases — show me his escalation pattern and predict what he'll do next"

### Route Taken
**Deep path** — requires profiling engine + behavioral analysis + temporal pattern extraction.

### Engines Invoked
1. **SQL Retrieval Engine** — Fetch all FIRs where "Arjun Reddy" or aliases appear as accused
2. **Behavioral Profiling Engine** — Extract MO signatures, target progression, tool sophistication
3. **Pattern Analysis Engine** — Temporal escalation curve, cooling-off periods
4. **Graph Intelligence Engine** — Associate network (co-accused, shared infrastructure)
5. **Search/Ranking Engine** — Similar offender profiles from national cybercrime database
6. **Timeline Engine** — Reconstruct complete criminal timeline

### Evidence Surfaced
| Item | Details |
|------|---------|
| FIRs | CC-2023-0089 (phishing, ₹45K), CC-2024-0156 (SIM swap fraud, ₹2.1L), CC-2024-0312 (fake KYC portal, ₹8.7L), CC-2025-0045 (corporate email compromise, ₹34L), CC-2025-0198 (supply chain invoice fraud, ₹1.2Cr) |
| Aliases | "Arjun Reddy", "Arjun R.", "AR Tech Solutions", "Arun Kumar" (ID docs) |
| Infrastructure | 3 shared hosting accounts, 2 domain registrars (fake company sites), 1 VPN provider |
| Escalation | Individual victims → small business → mid-size corporate → supply chain attack |
| Amount Progression | ₹45K → ₹2.1L → ₹8.7L → ₹34L → ₹1.2Cr (exponential growth) |
| Cooling Period | Decreasing: 8 months → 5 months → 3 months → 2 months |

### Intelligence Cards Generated
- **Offender Profile Card** — Complete behavioral dossier with risk score: CRITICAL (0.91)
- **Escalation Card** — Visual progression chart: phishing → SIM swap → fake portals → BEC → supply chain
- **MO Signature Card** — Technical fingerprint: specific phishing toolkit, domain naming pattern (*-secure.in), preferred registrar
- **Prediction Card** — Next likely: Large enterprise targeting (₹5Cr+), estimated within 45 days
- **Network Card** — 3 associates: Kiran P. (money mule), Sunil V. (domain registration), Meera D. (SIM procurement)

### Artifacts Produced
- **Criminal Timeline** — 30-month escalation timeline with sophistication markers
- **Behavioral Graph** — Skill/target/amount progression visualization
- **Risk Assessment** — Recidivism probability: 94%, violence escalation: LOW, financial escalation: CRITICAL
- **Similar Offenders** — 2 matching profiles from Hyderabad and Pune with identical toolkit signatures
- **Preventive Advisory** — Alert to major Bangalore corporates matching predicted target profile

### Proactive Alert
> 🟡 **ALERT:** New domain registration detected: "tataprojects-secure.in" — registrar matches Arjun Reddy's known pattern. Domain naming convention matches MO signature. Hosting on same provider as CC-2025-0198 infrastructure.

### Hypothesis Tested
**H1: "Is 'Arun Kumar' from CC-2024-0312 the same person as 'Arjun Reddy'?"**
- Supporting: 0.82 — same phishing toolkit fingerprint, overlapping IP ranges, similar domain pattern, shared hosting account
- Contradicting: 0.15 — different PAN number on record (likely forged)
- Verdict: **Strongly Supported**
- Missing: Biometric confirmation, device forensics

### Demo Talking Point
> "Traditional systems show isolated FIRs. Our system automatically builds a behavioral escalation profile showing this offender went from ₹45K phishing to ₹1.2 Crore supply chain fraud in 30 months — with decreasing cooling periods. It predicts his NEXT target type and timeframe, enabling preventive action."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 1: Conversational Intelligence | Natural language profiling request |
| Req 5: Offender Profiling | Complete behavioral dossier with escalation analysis |
| Req 3: Crime Pattern Analysis | Temporal escalation pattern, cooling period analysis |
| Req 6: Decision Support | Predictive advisory, preventive recommendations |
| Req 8: Crime Forecasting | Next-offense prediction with timeframe |
| Req 9: Explainable AI | Every escalation step cited to specific FIR |

---

## Scenario 3: UPI Fraud Money Trail

### Title and Crime Type
**UPI Fraud Money Trail** — IPC 420/BNS 318 (Cheating), IT Act 66C (Identity Theft), IT Act 66D (Cheating by Personation), PMLA (Prevention of Money Laundering Act)

### Officer Persona
**IO (Investigating Officer)** — Inspector Manjunath K., Koramangala PS, assigned FIR KOR-2026-0156

### Investigation Goal
Trace ₹12.3 Lakh from victim Lakshmi Devi's account through a chain of mule accounts to the final cash-out point; identify the beneficiary and intermediate handlers.

### Opening Query
> "Trace the money from victim Lakshmi Devi's UPI ID lakshmi.devi@okicici — show me where the ₹12.3 lakh went through all intermediate accounts"

### Route Taken
**Deep path** — multi-hop financial analysis requiring graph traversal and pattern detection.

### Engines Invoked
1. **Financial Analysis Engine** — Reconstruct transaction chain from source UPI to all downstream accounts
2. **Graph Intelligence Engine** — Build transaction graph, detect layering patterns, identify fan-out/fan-in
3. **Pattern Analysis Engine** — Identify structuring (sub-₹1L splits), velocity anomalies, circular flows
4. **SQL Retrieval Engine** — Fetch account holder details, KYC data, linked FIRs
5. **Behavioral Profiling Engine** — Profile mule accounts (lifespan, transaction patterns)
6. **Timeline Engine** — Reconstruct minute-by-minute flow

### Evidence Surfaced
| Item | Details |
|------|---------|
| Victim | Lakshmi Devi, UPI: lakshmi.devi@okicici, lost ₹12,30,000 on 15-Jul-2026 |
| Layer 1 | ₹12.3L → splits into: ₹4.5L to ramesh.fake@ybl, ₹4.3L to kumar.pay@paytm, ₹3.5L to shop.billing@okaxis |
| Layer 2 | ramesh.fake@ybl → ₹2.2L to crypto exchange, ₹2.3L to new.account77@oksbi |
| Layer 2 | kumar.pay@paytm → ₹4.3L to gold.shop.hsr@okicici (gold purchase, same day) |
| Layer 2 | shop.billing@okaxis → ₹1.8L cash withdrawal ATM (Jayanagar), ₹1.7L to wallet recharge |
| Final Beneficiary | Nagesh B. (aka "Naga"), Jayanagar — controls ramesh.fake@ybl and shop.billing@okaxis (same phone number in KYC) |
| Mule Accounts | 5 accounts, all opened within 60 days, minimal KYC, high velocity |
| Total Traced | ₹12.3L fully accounted: ₹2.2L crypto, ₹4.3L gold, ₹1.8L cash, ₹2.3L in transit, ₹1.7L wallet |

### Intelligence Cards Generated
- **Financial Trail Card** — Complete Sankey diagram showing ₹12.3L flow through 5 accounts across 3 layers
- **Mule Account Card** — 5 flagged accounts with creation date, KYC status, lifetime, transaction velocity
- **Layering Detection Card** — Structuring pattern: all Layer 1 transfers under ₹5L (reporting threshold avoidance)
- **Entity Card** — Nagesh B.: linked to 2 other fraud FIRs (KOR-2025-0445, HSR-2026-0067)
- **Cash-Out Card** — Methods: crypto (18%), gold (35%), ATM cash (15%), in-transit (19%), wallet (13%)

### Artifacts Produced
- **Sankey Flow Diagram** — ECharts Sankey showing source → Layer 1 → Layer 2 → cash-out with amounts and timestamps
- **Transaction Timeline** — Minute-by-minute reconstruction: initial fraud at 10:14 AM, Layer 1 splits at 10:17–10:22 AM, cash-out complete by 2:45 PM
- **Mule Network Graph** — Cytoscape.js graph showing account relationships and controller (Nagesh B.)
- **Freezing Recommendation** — Priority list: (1) new.account77@oksbi (₹2.3L still in transit), (2) wallet account (₹1.7L recoverable)
- **Investigation Package PDF** — Complete trail documentation for court submission

### Proactive Alert
> 🔴 **ALERT:** ₹2.3L in new.account77@oksbi showing outward transfer attempt to another new account. Immediate freezing recommended. Account holder attempting to move funds — 47 minutes since last activity.

### Hypothesis Tested
**H1: "Is Nagesh B. the mastermind or just another mule?"**
- Supporting (mastermind): 0.78 — controls 2 of 5 mule accounts, phone number links to 2 prior fraud FIRs, accounts opened in sequence suggesting planning
- Contradicting: 0.22 — no evidence of direct contact with victim, could be Layer 2 operator taking cut
- Verdict: **Weakly Supported** as mastermind; likely mid-level operator
- Missing: CDR analysis for communication with victim-facing caller, upstream handler identification

### Demo Talking Point
> "The officer asked 'where did the money go?' and within seconds got a complete Sankey diagram tracing ₹12.3 Lakh through 5 mule accounts to final cash-out — crypto, gold, and cash. The system identified ₹2.3L still in transit and recommended immediate freezing. This analysis would take a financial forensics team days; the system does it in seconds from pre-indexed transaction data."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 1: Conversational Intelligence | Natural language financial query |
| Req 7: Financial Crime Detection | Full money trail reconstruction, mule detection, layering identification |
| Req 2: Criminal Network Analysis | Transaction graph showing account controller relationships |
| Req 6: Decision Support | Freezing recommendations with priority and recoverability |
| Req 9: Explainable AI | Every transaction cited with timestamp, amount, account ID |

---

## Scenario 4: Chain Snatching Hotspot Forecast

### Title and Crime Type
**Chain Snatching Hotspot Forecast** — IPC 356/BNS 304 (Assault to commit theft/snatching), IPC 379/BNS 303 (Theft), IPC 392/BNS 309 (Robbery)

### Officer Persona
**DCP (Deputy Commissioner of Police)** — DCP Raghavendra Rao, Bangalore South Division

### Investigation Goal
Review the 30-day crime forecast for chain snatching in Bangalore South; identify predicted hotspot clusters; deploy patrol resources optimally based on time-of-day and location predictions.

### Opening Query
> "Show me the chain snatching forecast for Bangalore South for the next 30 days — where should I deploy extra patrols?"

### Route Taken
**Fast path** — structured forecasting query with pre-computed Prophet models; no ambiguity resolution needed.

### Engines Invoked
1. **Forecasting Engine** — Prophet model for IPC 356/379 in Bangalore South (30-day rolling forecast)
2. **Pattern Analysis Engine** — Spatial clustering (H3 hex resolution 8), temporal heatmap (hour × day)
3. **SQL Retrieval Engine** — Historical baseline: last 90 days chain snatching in division
4. **Graph Intelligence Engine** — Known active offenders in predicted hotspot areas (residence/hangout proximity)

### Evidence Surfaced
| Item | Details |
|------|---------|
| Forecast | 23 predicted incidents in next 30 days (vs 18 baseline = +28% increase, p<0.05) |
| Top Hotspots | (1) Jayanagar 4th Block Market, (2) Banashankari BDA Complex, (3) JP Nagar 6th Phase main road, (4) BTM Layout 2nd Stage |
| Peak Times | 6:30–8:30 AM (morning walkers), 5:30–7:30 PM (evening commuters) |
| Peak Days | Tuesday, Thursday, Saturday (market days correlate) |
| Seasonality | July–August spike: +34% vs annual average (shorter daylight, rain reduces witnesses) |
| Active Offenders | 4 known chain snatchers with recent release/bail in jurisdiction: Manju (bail 12-Jun), Srinivas K. (released 28-Jun), Raju D. (bail 05-Jul), Imran S. (released 01-Jul) |
| Confidence | 80% band: 18–28 incidents; 95% band: 14–32 incidents |

### Intelligence Cards Generated
- **Forecast Card** — 30-day prediction with confidence bands, comparison to baseline, trend direction
- **Hotspot Map Card** — H3 hexagonal overlay on MapLibre map with intensity gradient (red/orange/yellow)
- **Temporal Heatmap Card** — 7×24 grid showing predicted crime density by hour and day-of-week
- **Active Offender Card** — 4 recently released offenders with addresses near predicted hotspots
- **Sociological Context Card** — Correlation: market days + evening hours + low streetlight density = highest risk

### Artifacts Produced
- **H3 Hexagonal Hotspot Map** — Deck.gl visualization with predicted intensity per hex cell, filterable by week
- **Patrol Deployment Plan** — Recommended beat allocation: 2 extra patrols in Jayanagar (6–9 AM), 3 in Banashankari (5–8 PM), mobile unit for JP Nagar/BTM
- **Prophet Forecast Chart** — ECharts line chart with observed data, forecast, 80% and 95% confidence bands
- **Temporal Heatmap** — ECharts 7×24 heatmap showing crime probability density
- **Resource Allocation PDF** — Exportable deployment order with justification and evidence

### Proactive Alert
> 🟡 **ALERT:** Chain snatching forecast for Week 2 (Jul 28–Aug 3) shows spike to 8 predicted incidents — 2.1x the weekly average. Coincides with Varamahalakshmi festival week (more women wearing gold). Recommend enhanced deployment starting Jul 27.

### Hypothesis Tested
N/A — This is a forecasting/resource allocation scenario, not a hypothesis-driven investigation.

### Demo Talking Point
> "The DCP asked one question and got a complete 30-day deployment strategy — hexagonal hotspot maps, peak time windows, known offenders in the area, and even seasonal context (festival week spike). This transforms reactive policing into proactive prevention. The Prophet model shows 28% increase predicted with 80% confidence."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 1: Conversational Intelligence | Natural language query for strategic planning |
| Req 8: Crime Forecasting | Prophet 30-day forecast with confidence bands |
| Req 3: Crime Pattern Analysis | H3 spatial clustering, temporal heatmap, seasonality |
| Req 4: Sociological Insights | Market day correlation, streetlight density, festival context |
| Req 6: Decision Support | Patrol deployment recommendations with justification |
| Req 9: Explainable AI | Forecast methodology transparent, confidence bands visible |

---

## Scenario 5: Hypothesis — Are These Robberies Connected?

### Title and Crime Type
**Linked Robbery Hypothesis** — IPC 392/BNS 309 (Robbery), IPC 397/BNS 310 (Robbery with attempt to cause death), IPC 34/BNS 3(5) (Common Intention)

### Officer Persona
**SHO (Station House Officer)** — SHO Inspector Basavaraju M., Indiranagar PS

### Investigation Goal
Test whether 3 recent robberies in his jurisdiction (different MOs on surface) are actually committed by the same group; get a structured evidence-based evaluation, not a gut-feeling confirmation.

### Opening Query
> "I think these three robbery cases might be connected — FIR IND-2026-0078, IND-2026-0092, and IND-2026-0104. Can you check if they're linked?"

### Route Taken
**Deep path** — hypothesis evaluation requiring multi-engine evidence gathering and structured reasoning.

### Engines Invoked
1. **SQL Retrieval Engine** — Pull complete FIR details for all 3 cases
2. **Graph Intelligence Engine** — Check shared entities (accused, witnesses, phone numbers, vehicles, locations)
3. **Pattern Analysis Engine** — Compare MO signatures, timing, target selection
4. **Search/Ranking Engine** — Find similar linked robbery series in historical data
5. **Behavioral Profiling Engine** — Build composite MO from the 3 FIRs, check consistency
6. **Timeline Engine** — Reconstruct chronology and check feasibility of single-group execution

### Evidence Surfaced
| Item | Details |
|------|---------|
| FIR IND-2026-0078 | 03-Jul, 9:45 PM, Indiranagar 100ft Road — 2 men on black Pulsar, gold chain snatched from woman, ₹1.8L |
| FIR IND-2026-0092 | 11-Jul, 10:15 PM, CMH Road — 2 men on dark bike, phone + wallet snatched from pedestrian, ₹35K |
| FIR IND-2026-0104 | 18-Jul, 9:30 PM, HAL Airport Road — 2 men on black motorcycle, handbag snatched from car window, ₹2.4L + jewelry |
| Shared Pattern | 2-person bike team, 9:30–10:15 PM window, 7-day interval, same general area (3 km radius) |
| CCTV Partial | Black Pulsar 220 (partial plate: KA-03-M_-_8XX) visible in 2 of 3 locations |
| Witness Description | "Slim rider, stocky pillion" — consistent across all 3 FIRs |
| Dissimilarity | Target type varies (woman/pedestrian/car), items taken vary (chain/phone/bag) |
| Phone Tower | Same tower sector (Indiranagar East) active at time of all 3 incidents for IMSI 4048XXXXXXXX |

### Intelligence Cards Generated
- **Hypothesis Evaluation Card** — Structured for/against evidence with confidence score
- **Pattern Comparison Card** — Side-by-side MO comparison table across 3 FIRs
- **Entity Overlap Card** — Shared entities: black Pulsar (2/3 confirmed), IMSI match (3/3), physical description (3/3)
- **Timeline Feasibility Card** — 7-day interval pattern, all within travel distance

### Artifacts Produced
- **Hypothesis Report** — Structured evaluation document:
  ```
  Hypothesis: "FIR-078, FIR-092, and FIR-104 are committed by the same 2-person team"
  
  SUPPORTING EVIDENCE (Strength: 0.84)
  ├── Same vehicle type + partial plate match (2/3 FIRs) — weight: 0.25
  ├── Same IMSI in cell tower at crime time (3/3 FIRs) — weight: 0.30
  ├── Consistent physical descriptions (3/3 FIRs) — weight: 0.15
  ├── 7-day regular interval pattern — weight: 0.08
  └── Same time window (9:30–10:15 PM) — weight: 0.06
  
  CONTRADICTING EVIDENCE (Strength: 0.16)
  ├── Target type varies (women, men, vehicles) — weight: 0.10
  └── Items taken are opportunistic, not consistent — weight: 0.06
  
  VERDICT: STRONGLY SUPPORTED (84% confidence)
  
  MISSING EVIDENCE (would increase confidence)
  ├── Full number plate confirmation from CCTV enhancement
  ├── CDR analysis for IMSI 4048XXXXXXXX
  └── Informant confirmation of suspects
  
  SUGGESTED NEXT ACTIONS
  1. Request CCTV enhancement for plate confirmation
  2. CDR request for IMSI 4048XXXXXXXX (all 3 dates)
  3. Deploy decoy team on 25-Jul (predicted next date, 7-day interval)
  4. Check pawnshops in Indiranagar/Domlur for stolen items
  ```
- **Prediction** — Next incident likely: 25-Jul-2026, 9:30–10:15 PM, within 3 km of Indiranagar
- **Composite Sketch Request** — Auto-generated request combining witness descriptions

### Proactive Alert
> 🔴 **ALERT:** It is 24-Jul-2026. Based on the 7-day interval pattern, the predicted next incident window is TOMORROW (25-Jul, 9:30–10:15 PM, Indiranagar area). Recommend deploying decoy team tonight for surveillance.

### Hypothesis Tested
**H1: "Are FIR-078, FIR-092, and FIR-104 committed by the same 2-person team?"**
- Supporting evidence strength: **0.84**
- Contradicting evidence strength: **0.16**
- Verdict: **Strongly Supported**
- Alternative explanation: "Copycat inspired by news reports" — evaluated at 0.11 probability (robberies not reported in media)

### Demo Talking Point
> "The SHO had a hunch that 3 cases were connected. Instead of confirming bias, the system provides STRUCTURED evaluation — weighted evidence for and against, a confidence score of 84%, and explicitly identifies what's missing. It even predicts the next incident date based on the interval pattern. This is AI augmenting human intuition with rigorous evidence analysis."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 1: Conversational Intelligence | Natural language hypothesis submission |
| Req 6: Decision Support | Structured hypothesis evaluation with ranked next actions |
| Req 3: Crime Pattern Analysis | Temporal interval detection, MO comparison |
| Req 8: Crime Forecasting | Next-incident prediction based on interval pattern |
| Req 9: Explainable AI | Weighted evidence, confidence score, contradictions surfaced |
| Req 5: Offender Profiling | Composite MO profile from linked cases |

---

## Scenario 6: Proactive Alert — New FIR Matches Active Case

### Title and Crime Type
**Proactive Alert: New FIR Matches Active UPI Fraud Case** — IT Act 66C, 66D, IPC 420/BNS 318 (Cheating)

### Officer Persona
**IO (Investigating Officer)** — SI Deepika N., Electronic City PS, investigating FIR EC-2026-0234 (UPI fraud, ₹8.7L)

### Investigation Goal
This scenario demonstrates the SYSTEM's proactive capability — not officer-initiated. The system detects that a newly filed FIR contains a UPI ID already flagged in SI Deepika's active investigation and pushes an alert.

### Opening Query
> *(No officer query — this is a system-initiated alert)*

**System-initiated notification:**
> "🔴 New FIR HSR-2026-0189 filed at HSR Layout PS contains UPI ID 'quickpay.merchant@ybl' — this UPI ID is a flagged mule account in your active case EC-2026-0234. New victim: Suresh Babu, ₹3.2L defrauded."

### Route Taken
**Background workflow (Catalyst Signals)** — triggered by FIR ingestion event, not by user query.

### Engines Invoked
1. **SQL Retrieval Engine** — Match new FIR entities against active investigation watchlists (triggered by Catalyst Signals on FIR insert)
2. **Graph Intelligence Engine** — Check if new FIR entities connect to any active investigation graph
3. **Financial Analysis Engine** — Check if new transaction accounts overlap with known mule network
4. **Search/Ranking Engine** — Semantic similarity between new FIR narrative and active cases
5. **Evidence/Explainability Engine** — Validate match quality before alerting (avoid false positives)

### Evidence Surfaced
| Item | Details |
|------|---------|
| New FIR | HSR-2026-0189, filed 24-Jul-2026 at 11:30 AM by Suresh Babu, HSR Layout |
| Match Type | UPI ID: quickpay.merchant@ybl — appears in both FIRs as recipient of fraud proceeds |
| Active Case | EC-2026-0234: ₹8.7L UPI fraud, quickpay.merchant@ybl identified as Layer 1 mule |
| New Victim | Suresh Babu, ₹3.2L transferred to quickpay.merchant@ybl via fake refund scheme |
| Combined Exposure | Same mule account received: ₹8.7L (EC case) + ₹3.2L (HSR case) = ₹11.9L total |
| Additional Link | Phone number in HSR FIR (+91-98454-XXXXX) matches a witness contact in EC case |
| Temporal Pattern | EC fraud: 18-Jul, HSR fraud: 23-Jul — mule account active again within 5 days |

### Intelligence Cards Generated
- **Alert Card** — High-priority match notification with evidence summary and match confidence (0.94)
- **Connection Card** — Visual showing EC-2026-0234 ↔ HSR-2026-0189 linked through shared UPI ID
- **Updated Financial Trail Card** — Combined Sankey now showing 2 victims feeding same mule network
- **Urgency Card** — Account still active; last outward transfer 2 hours ago; freezing window closing

### Artifacts Produced
- **Push Notification** — Real-time SSE alert to SI Deepika's workspace
- **Updated Investigation Graph** — Auto-merged new FIR into existing investigation graph
- **Combined Victim List** — 2 victims (potentially more), total exposure ₹11.9L+
- **Freezing Request Draft** — Pre-generated account freeze request for quickpay.merchant@ybl with combined evidence from both FIRs
- **Cross-Station Coordination Note** — Auto-generated note suggesting joint investigation with HSR Layout PS IO

### Proactive Alert
> 🔴 **PROACTIVE ALERT (System-Initiated):**
> New FIR HSR-2026-0189 matches your active investigation EC-2026-0234.
> **Match: UPI ID quickpay.merchant@ybl** (mule account in your case)
> New victim: Suresh Babu, ₹3.2L defrauded 23-Jul-2026.
> ⚠️ Mule account showed outward transfer activity 2 hours ago — freezing window may be closing.
> **Recommended actions:** (1) Request immediate freeze, (2) Contact HSR PS IO for coordination, (3) Update chargesheet with additional victim.

### Hypothesis Tested
N/A — This is a pattern-matching alert, not a hypothesis scenario. However, the system auto-evaluates:
**"Are EC-2026-0234 and HSR-2026-0189 part of the same fraud operation?"** → Confidence: 0.94 (shared mule account + temporal proximity + same MO)

### Demo Talking Point
> "Nobody asked the system anything. A new FIR was filed at a DIFFERENT police station, and within seconds the system automatically detected that a UPI ID in the new FIR matches a mule account in an active investigation elsewhere. It pushed a real-time alert with recommended actions. This is the difference between reactive policing and proactive intelligence — the system connects dots across station boundaries automatically."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 7: Financial Crime Detection | UPI mule account matching across cases |
| Req 6: Decision Support | Auto-generated freezing recommendation with urgency |
| Req 2: Criminal Network Analysis | Auto-merge of new evidence into investigation graph |
| Req 8: Crime Forecasting | Temporal pattern (5-day reuse cycle) suggests imminent next victim |
| Req 9: Explainable AI | Match confidence score with explicit evidence basis |
| Req 10: RBAC | Alert routed only to assigned IO, not broadcast |

---

## Scenario 7: Entity Resolution — Same Suspect, Different Names

### Title and Crime Type
**Entity Resolution: Same Suspect, Different Names** — IPC 379/BNS 303 (Theft), IPC 454/BNS 329 (Lurking house-trespass), IPC 457/BNS 331 (Lurking house-trespass by night to commit offence)

### Officer Persona
**Analyst** — Crime Analyst Naveen Kumar, Central Crime Branch, Bangalore

### Investigation Goal
Investigate system-flagged entity resolution: the system has identified that 'Rajesh K.', 'Rajesh Kumar', 'R. Kumar', and 'Rajesh Kumara Swamy' across 4 FIRs from different stations are likely the same person. Validate and merge records.

### Opening Query
> "The system flagged a possible entity match — show me the evidence that 'Rajesh K.' and 'Rajesh Kumar' are the same person"

### Route Taken
**Fast path** — entity resolution is pre-computed; this retrieves the resolution card with supporting evidence.

### Engines Invoked
1. **SQL Retrieval Engine** — Fetch all FIRs containing name variants matching the entity cluster
2. **Graph Intelligence Engine** — Check shared attributes: address, phone, age, physical description, associate overlap
3. **Search/Ranking Engine** — Semantic similarity of FIR narratives mentioning each variant
4. **Pattern Analysis Engine** — MO consistency check across FIRs attributed to name variants
5. **Evidence/Explainability Engine** — Compute resolution confidence with weighted attribute matching

### Evidence Surfaced
| Item | Details |
|------|---------|
| FIR 1 | IND-2025-0334: "Rajesh K., age 32, Domlur" — house break, ₹85K jewelry stolen |
| FIR 2 | KOR-2025-0567: "Rajesh Kumar, age 33, Domlur 2nd Stage" — house break, ₹1.2L electronics |
| FIR 3 | HSR-2026-0045: "R. Kumar, age 32, address not provided" — attempted break-in, fled |
| FIR 4 | WF-2026-0201: "Rajesh Kumara Swamy, age 33, Domlur" — house break, ₹2.1L |
| Shared Phone | +91-99002-XXXXX appears in FIR 1 (accused contact) and FIR 4 (CDR hit near scene) |
| Address Match | "Domlur" / "Domlur 2nd Stage" — within 500m, consistent across 3 of 4 FIRs |
| Age Consistency | 32-33 across all 4 FIRs (1-year variance, consistent with filing over 14 months) |
| Physical Description | "5'8", medium build, scar on left forearm" — mentioned in FIR 1 and FIR 2 |
| MO Match | All 4: night-time house break-in, ground floor, tool marks consistent with crowbar, jewelry/electronics targeted |
| Associate Overlap | "Shankar" mentioned as co-accused in FIR 1 and FIR 4 |

### Intelligence Cards Generated
- **Entity Resolution Card** — Side-by-side comparison table of all name variants with matching attributes highlighted
- **Resolution Confidence Card** — Weighted scoring: name similarity (0.85) + address (0.90) + phone (0.75) + age (0.95) + MO (0.82) + associate (0.70) = **Overall: 0.88**
- **Merged Profile Card** — Consolidated offender profile (post-confirmation)
- **Impact Card** — "If confirmed, this individual has 4 FIRs (not 1), making him a habitual offender under IPC 75/BNS 9"

### Artifacts Produced
- **Resolution Evidence Matrix** — Table showing attribute-by-attribute match across all 4 FIR records
  ```
  Attribute        | IND-0334      | KOR-0567        | HSR-0045    | WF-0201
  Name             | Rajesh K.     | Rajesh Kumar    | R. Kumar    | Rajesh Kumara Swamy
  Age              | 32            | 33              | 32          | 33
  Address          | Domlur        | Domlur 2nd Stg  | —           | Domlur
  Phone            | 99002-XXXXX   | —               | —           | 99002-XXXXX (CDR)
  Scar             | Left forearm  | Left forearm    | —           | —
  MO               | Night/crowbar | Night/crowbar   | Night/tool  | Night/crowbar
  Co-accused       | Shankar       | —               | —           | Shankar
  ```
- **Merge Action** — One-click merge into unified entity with all FIRs linked (pending analyst confirmation)
- **Habitual Offender Flag** — Auto-generated flag: 4+ FIRs same category = habitual offender under IPC 75
- **Updated Network Graph** — Merged node now shows connections to associate "Shankar" and all 4 crime locations

### Proactive Alert
> 🟡 **ALERT:** Entity resolution batch run completed. 12 new potential entity clusters detected across last month's FIRs. 3 high-confidence (>0.85), 5 medium (0.65–0.85), 4 low (0.50–0.65). "Rajesh K./Kumar" cluster is highest priority (0.88 confidence, habitual offender implication).

### Hypothesis Tested
**H1: "Are 'Rajesh K.', 'Rajesh Kumar', 'R. Kumar', and 'Rajesh Kumara Swamy' the same individual?"**
- Supporting: 0.88 — name phonetic similarity, shared phone, overlapping address, consistent age, matching MO, shared associate
- Contradicting: 0.12 — "Rajesh Kumar" is a very common name; HSR FIR has minimal identifying details
- Verdict: **Strongly Supported**
- Missing: Fingerprint/photo comparison (would raise to 0.95+), Aadhaar cross-reference

### Demo Talking Point
> "In Indian policing, the same criminal appears with spelling variations across different station FIRs — 'Rajesh K.' at one station, 'Rajesh Kumar' at another. Our entity resolution engine automatically detects these using weighted multi-attribute matching (phone, address, age, MO, associates) and flags them. Here, it identified a single person across 4 FIRs who qualifies as a habitual offender — something no manual system would catch across different jurisdictions."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 2: Criminal Network Analysis | Entity merging reveals true network structure |
| Req 5: Offender Profiling | Merged profile reveals habitual offender status |
| Req 3: Crime Pattern Analysis | MO consistency analysis across fragmented records |
| Req 9: Explainable AI | Weighted confidence scoring with per-attribute breakdown |
| Req 6: Decision Support | Habitual offender flag, merge recommendation |
| Req 1: Conversational Intelligence | Natural language exploration of resolution evidence |

---

## Scenario 8: Drug Network Discovery

### Title and Crime Type
**Drug Network Discovery** — NDPS Act Sections 20 (Cannabis), 22 (Psychotropic substances), 27A (Financing illicit traffic), 29 (Criminal conspiracy for NDPS offences)

### Officer Persona
**Analyst** — Senior Intelligence Analyst Ramesh Gowda, Anti-Narcotics Wing, Bangalore City

### Investigation Goal
Use graph analysis to uncover the full structure of a suspected drug distribution network in East Bangalore — from supplier through mid-level dealers to street pushers — using shared phone contacts, transaction patterns, and co-arrest history.

### Opening Query
> "Starting from arrested dealer Imran Pasha (FIR KRP-2026-0089), show me his full network — phone contacts, transaction links, co-accused across all NDPS cases in East Bangalore"

### Route Taken
**Deep path** — multi-hop graph expansion with community detection and financial pattern analysis.

### Engines Invoked
1. **Graph Intelligence Engine** — 3-hop expansion from Imran Pasha node; Louvain community detection; PageRank for kingpin identification; betweenness centrality for bridge nodes
2. **SQL Retrieval Engine** — All NDPS FIRs in East Bangalore (KR Puram, Whitefield, Mahadevapura, Ramamurthy Nagar) last 18 months
3. **Financial Analysis Engine** — Transaction pattern analysis: regular small payments (wages), irregular large payments (supply purchase)
4. **Pattern Analysis Engine** — Temporal patterns of arrests, supply chain timing
5. **Behavioral Profiling Engine** — Role classification based on behavior: supplier/dealer/pusher/financier
6. **Search/Ranking Engine** — Similar network structures in NCB database
7. **Timeline Engine** — Network evolution over 18 months

### Evidence Surfaced
| Item | Details |
|------|---------|
| FIRs Linked | 8 NDPS FIRs across 4 stations: KRP-2026-0089, KRP-2026-0034, KRP-2025-0445, WF-2025-0312, WF-2025-0178, MDP-2025-0267, MDP-2026-0056, RMN-2025-0134 |
| Network Size | 15 members identified across 3 hierarchical layers |
| Kingpin | "Saleem Bhai" (not directly in any FIR) — identified through PageRank (0.41) + financial hub analysis. Phone contacts with 6 of 15 members, no direct drug handling |
| Layer 1 (Supply) | Saleem Bhai (kingpin), Farooq M. (logistics), Kavitha S. (finance/hawala) — 3 members |
| Layer 2 (Distribution) | Imran Pasha, Ravi T., Suresh Naik, Nagesh D., Venkatesh P. — 5 members |
| Layer 3 (Street) | 7 identified street pushers (college area operators) |
| Financial Pattern | Regular ₹15K–₹25K payments from Layer 2 to Kavitha S.'s account (every 3–4 days) = supply restocking |
| Phone Clusters | Louvain detected 3 communities matching Layer 1/2/3 hierarchy exactly |
| Bridge Node | Imran Pasha: highest betweenness centrality (0.38) — connects Layer 1 to Layer 3; arresting him fragments network |
| Supply Chain | Goa → Saleem (Bhai) → Layer 2 dealers → college campuses (Whitefield, KR Puram) |

### Intelligence Cards Generated
- **Network Structure Card** — 15-node hierarchical graph with role labels, community coloring, centrality sizing
- **Kingpin Identification Card** — "Saleem Bhai": PageRank 0.41, 0 FIRs but connected to 6 network members; likely controls supply
- **Bridge Node Card** — Imran Pasha: betweenness 0.38; removal fragments network into 2 disconnected components
- **Financial Pattern Card** — Regular payment cycle (₹15K–₹25K every 3–4 days) from 5 Layer 2 members to single hawala account
- **Vulnerability Card** — Network fragmentation analysis: arresting Imran Pasha + Kavitha S. disconnects supply from distribution
- **Evolution Card** — Network grew from 5 to 15 members over 18 months; 3 new pushers added in last 2 months (expansion phase)

### Artifacts Produced
- **Hierarchical Network Graph** — Cytoscape.js force-directed layout with:
  - Node size = PageRank score
  - Node color = Louvain community (Layer 1: red, Layer 2: orange, Layer 3: yellow)
  - Edge thickness = interaction frequency
  - Edge labels = relationship type (phone/financial/co-arrest)
- **Sankey Diagram** — Money flow from street sales → Layer 2 → Kavitha S. (hawala) → upstream
- **Network Vulnerability Report** — Optimal disruption strategy: "Arrest order: (1) Kavitha S. (finance), (2) Imran Pasha (bridge), (3) Saleem Bhai (kingpin)"
- **Timeline** — 18-month network evolution showing recruitment waves and expansion phases
- **Surveillance Targets** — Prioritized list with addresses, known schedules, and proximity to schools/colleges

### Proactive Alert
> 🔴 **ALERT:** New NDPS FIR filed at Ramamurthy Nagar (RMN-2026-0098) — arrested individual "Anil K." has phone contact with 2 known Layer 3 members. Possible new pusher recruited into Saleem network. Network may be expanding to Ramamurthy Nagar area.

### Hypothesis Tested
**H1: "Is 'Saleem Bhai' the network kingpin despite appearing in zero FIRs?"**
- Supporting: 0.79 — highest PageRank (0.41), phone contact with 6/15 members across all layers, financial flows trace upstream to contacts linked to him, informant intelligence matches
- Contradicting: 0.21 — no direct evidence of drug handling, no FIR, no financial account in his name (uses hawala through Kavitha S.)
- Verdict: **Strongly Supported** as network controller
- Missing: Direct surveillance evidence, intercepted communications, financial forensics on Kavitha S.'s accounts

### Demo Talking Point
> "Starting from ONE arrested street dealer, graph analysis uncovered a 15-member hierarchical network — including a kingpin who appears in ZERO FIRs. Traditional investigation would never find 'Saleem Bhai' because he never touches the drugs. But PageRank centrality analysis reveals he's the most important node. The system also identifies the optimal arrest sequence to fragment the network: take out the finance person and the bridge node first."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 2: Criminal Network Analysis | Full community detection, PageRank, betweenness, hierarchical structure |
| Req 7: Financial Crime Detection | Supply chain payment pattern analysis, hawala detection |
| Req 5: Offender Profiling | Role classification (kingpin/dealer/pusher/financier) |
| Req 3: Crime Pattern Analysis | Temporal recruitment patterns, supply cycle timing |
| Req 6: Decision Support | Optimal disruption strategy with arrest sequence |
| Req 9: Explainable AI | Every connection cited to specific evidence (phone/financial/co-arrest) |
| Req 1: Conversational Intelligence | Natural language network exploration query |

---

## Scenario 9: Investigation Handover

### Title and Crime Type
**Investigation Handover — Complete Case Transfer** — IPC 302/BNS 103 (Murder), IPC 364/BNS 137 (Kidnapping), IPC 201/BNS 238 (Causing disappearance of evidence)

### Officer Persona
**IO (Outgoing)** — Inspector Suresh Hegde, transferred from Yelahanka PS
**IO (Incoming)** — SI Ananya Rao, newly assigned to case YEL-2025-0234

### Investigation Goal
Outgoing IO exports the complete investigation state — all evidence gathered, hypotheses tested, leads pursued (and dead ends), network analysis, timeline — so incoming IO can continue seamlessly without re-doing work or losing institutional knowledge.

### Opening Query
**Outgoing IO:**
> "Generate a complete handover package for case YEL-2025-0234 — include everything: timeline, evidence board, network graph, leads status, hypotheses, and what I'd recommend focusing on next"

**Incoming IO (after receiving package):**
> "Summarize the current state of case YEL-2025-0234 — what's been done, what's pending, and what should I do first?"

### Route Taken
**Fast path** (export) — deterministic compilation of investigation state from checkpoint.
**Fast path** (import/summary) — retrieval and summarization of handover package.

### Engines Invoked
1. **SQL Retrieval Engine** — Fetch complete investigation state: FIRs, evidence items, officer notes, query history
2. **Timeline Engine** — Compile chronological investigation timeline (both crime events AND investigation actions)
3. **Graph Intelligence Engine** — Export current network graph state (nodes pinned, expansions done, communities identified)
4. **Evidence/Explainability Engine** — Compile all evidence with provenance, citation chains, and confidence levels
5. **Search/Ranking Engine** — Gather similar case outcomes for context

### Evidence Surfaced
| Item | Details |
|------|---------|
| Case | YEL-2025-0234: Missing person Anand Rao (32), last seen 14-Nov-2025, Yelahanka New Town |
| Duration | 8 months active investigation by Inspector Hegde |
| FIRs Connected | YEL-2025-0234 (primary), YEL-2025-0267 (suspicious vehicle), BYP-2025-0445 (unidentified body — excluded) |
| Evidence Items | 34 items catalogued: 12 witness statements, 8 CDR analyses, 6 CCTV clips, 4 forensic reports, 4 financial records |
| Leads | 11 total: 5 closed (dead ends documented), 3 active (with priority), 3 new (untouched) |
| Hypotheses | H1: Kidnapping for ransom (REJECTED — no demand in 8 months), H2: Business partner dispute (ACTIVE, 0.62 confidence), H3: Voluntary disappearance (WEAKLY SUPPORTED, 0.34) |
| Network | 8-node graph: victim, wife, business partner Mahesh G., 2 employees, driver, unknown caller, mystery vehicle owner |
| Key Suspect | Mahesh G. (business partner) — ₹45L financial dispute, last person to speak to victim (CDR), alibi has gaps |

### Intelligence Cards Generated
- **Handover Summary Card** — One-page case status: 8 months, 34 evidence items, 3 active leads, 1 primary suspect
- **Investigation Timeline Card** — Dual timeline: crime events (Nov 2025) + investigation milestones (Nov 2025–Jul 2026)
- **Evidence Board Card** — All 34 items organized by category with confidence and relevance scores
- **Hypothesis Status Card** — All 3 hypotheses with current verdict and evidence basis
- **Lead Priority Card** — Ranked leads: (1) Mahesh G. financial forensics, (2) Unknown caller identification, (3) CCTV from highway toll

### Artifacts Produced
- **Complete Handover Package PDF** (23 pages):
  ```
  1. Executive Summary (1 page)
  2. Crime Event Timeline (2 pages)
  3. Investigation Action Log (3 pages)
  4. Evidence Inventory with Citations (5 pages)
  5. Network Analysis & Graph (2 pages)
  6. Hypothesis Evaluations (3 pages)
  7. Lead Status & Recommendations (3 pages)
  8. Dead Ends & Why (2 pages) ← saves incoming IO from repeating work
  9. Outgoing IO's Assessment & Next Steps (2 pages)
  ```
- **Interactive Investigation State** — Full checkpoint restored in incoming IO's workspace
- **Evidence Board** — Visual board with all pinned entities, connections, and annotations preserved
- **Prioritized Next Actions:**
  1. "Get Mahesh G.'s business account statements (Apr–Nov 2025) — request pending since 3 weeks"
  2. "CCTV from Bellary Road toll — requisition submitted, follow up with NHAI"
  3. "Identify unknown caller (+91-80456-XXXXX) — 3 calls to victim on last day, unregistered SIM"

### Proactive Alert
> 🟡 **ALERT (to incoming IO):** Pending requisition for Mahesh G.'s bank statements (submitted 03-Jul-2026) has been pending 21 days. SLA typically 14 days. Recommend escalation to DCP for expedited order.

### Hypothesis Tested
**Current active hypothesis (transferred to incoming IO):**
**H2: "Business partner Mahesh G. is responsible for Anand Rao's disappearance"**
- Supporting: 0.62 — ₹45L dispute, last CDR contact, alibi gaps (3 hours unaccounted), business would benefit Mahesh if Anand declared dead
- Contradicting: 0.38 — no direct physical evidence, no witness to confrontation, Mahesh cooperated with initial inquiry
- Verdict: **Weakly Supported** — needs financial forensics to strengthen or eliminate
- Missing: Bank statements (pending), highway CCTV (pending), phone location data for gap hours

### Demo Talking Point
> "In Indian policing, investigation transfers lose critical context — the incoming IO starts from scratch. Our system preserves EVERYTHING: 8 months of work, 34 evidence items, tested hypotheses (including dead ends), and a prioritized action list. The incoming officer gets a one-line brief: 'Focus on the business partner's finances — here's exactly why and what's been tried.' This eliminates the #1 cause of stalled investigations: institutional knowledge loss during transfers."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 6: Decision Support | Prioritized handover with recommended next actions |
| Req 1: Conversational Intelligence | Natural language handover request and status query |
| Req 9: Explainable AI | Complete evidence provenance, dead ends documented, reasoning preserved |
| Req 2: Criminal Network Analysis | Investigation graph state preserved across transfer |
| Req 10: RBAC | Handover only to authorized incoming IO; audit trail of transfer |

---

## Scenario 10: Strategic Briefing

### Title and Crime Type
**District-Wide Strategic Intelligence Briefing** — All crime categories (IPC/BNS/Special Acts), district-level aggregate analysis

### Officer Persona
**SP (Superintendent of Police)** — SP Dr. Lakshmi Prasad, Bangalore Urban District

### Investigation Goal
Request a comprehensive monthly intelligence briefing covering: district-wide crime trends, forecasts for next 30 days, top active criminal networks, resource allocation recommendations, and emerging threats — suitable for presentation to DGP or district review meeting.

### Opening Query
> "Give me the monthly intelligence briefing for Bangalore Urban — trends, forecasts, top networks, hotspots, and where I should reallocate resources for August"

### Route Taken
**Deep path** — multi-engine aggregation requiring parallel execution of forecasting, pattern, network, and statistical engines across district scope.

### Engines Invoked
1. **SQL Retrieval Engine** — District-wide FIR aggregates: category counts, station-wise breakdown, month-over-month changes
2. **Forecasting Engine** — Prophet models for all major crime categories × division (30-day forecasts)
3. **Pattern Analysis Engine** — Spatial hotspot evolution, temporal anomalies, emerging patterns
4. **Graph Intelligence Engine** — Top active networks by size, recent activity, and threat level
5. **Behavioral Profiling Engine** — Top 10 high-risk offenders currently on bail/recently released
6. **Financial Analysis Engine** — Aggregate financial crime exposure and trends
7. **Search/Ranking Engine** — Comparison with same period last year, national benchmarks

### Evidence Surfaced
| Item | Details |
|------|---------|
| Total FIRs (Jul 2026) | 4,847 (↑6% vs Jun, ↑3% vs Jul 2025) |
| Top Category Increase | Chain snatching: +34% (187 → 251 cases) — seasonal spike confirmed |
| Top Category Decrease | Burglary: -12% (445 → 391 cases) — successful patrol deployment in May |
| Emerging Threat | Cybercrime (IT Act): +67% YoY (89 → 149 cases), fastest growing category |
| Hotspot Shift | Vehicle theft hotspot migrating from Whitefield → Marathahalli (3-month trend) |
| Top Networks | (1) Saleem drug network (15 members, active), (2) Vehicle theft ring (7 members, partially disrupted), (3) Online fraud syndicate (est. 10+ members, emerging) |
| Resource Gap | Koramangala PS: 23% above avg caseload, 15% below avg staff — critical mismatch |
| Forecast (Aug) | +8% overall predicted; chain snatching +28% (festival season); cybercrime +12% (trending) |
| Clearance Rate | District: 42% (vs 38% state average); Yelahanka division lagging at 31% |
| High-Risk Bail | 14 high-risk offenders currently on bail; 4 in predicted hotspot areas |

### Intelligence Cards Generated
- **District Dashboard Card** — Key metrics: total FIRs, clearance rate, forecast, top concerns
- **Trend Analysis Card** — Month-over-month and year-over-year trends for top 8 crime categories
- **Forecast Card** — 30-day predictions for all major categories with confidence bands
- **Hotspot Evolution Card** — Animated 6-month hotspot migration maps for top 3 crime types
- **Network Threat Card** — Top 3 active networks with size, threat level, and disruption status
- **Resource Mismatch Card** — Station-wise caseload vs. staffing analysis with recommendations
- **Sociological Context Card** — Demographic correlations: cybercrime concentrated in IT corridors, snatching in residential markets

### Artifacts Produced
- **Monthly Intelligence Briefing PDF** (12 pages):
  ```
  BANGALORE URBAN DISTRICT — MONTHLY INTELLIGENCE BRIEFING
  Period: July 2026 | Classification: FOR OFFICIAL USE ONLY
  
  1. Executive Summary & Key Metrics (1 page)
  2. Crime Trends — Category Analysis (2 pages)
     - Charts: bar (category comparison), line (6-month trend), YoY
  3. Spatial Analysis — Hotspot Maps (2 pages)
     - H3 hexagonal maps for top 5 crime types
     - Migration arrows showing hotspot movement
  4. Forecasts — August 2026 Predictions (2 pages)
     - Prophet forecasts with confidence bands
     - Festival calendar overlay (Varamahalakshmi, Independence Day)
  5. Network Intelligence (2 pages)
     - Top 3 active networks: structure, threat, recommended action
  6. Resource Allocation Recommendations (2 pages)
     - Station rebalancing proposal
     - Patrol deployment for predicted hotspots
     - Specialist team assignments
  7. Emerging Threats & Watch Items (1 page)
     - Cybercrime acceleration
     - New drug network expansion
     - Interstate gang movements
  ```
- **Interactive Dashboard** — ECharts-powered district dashboard with drill-down capability
- **Resource Allocation Matrix** — Station × crime type × forecast → optimal deployment table
- **Comparison Benchmark** — Bangalore Urban vs. state average vs. national metro average

### Proactive Alert
> 🔵 **STRATEGIC ALERT:** Independence Day (Aug 15) security planning window opening. Historical data shows +45% public gathering incidents in 7-day window. Recommend early deployment planning for parade routes and VIP movement corridors.

### Hypothesis Tested
N/A — This is a strategic intelligence aggregation scenario, not hypothesis-driven.

### Demo Talking Point
> "The SP asked one question and got a complete strategic intelligence package — 4,847 FIRs distilled into actionable insights: which crimes are rising, where they'll happen next month, which networks to prioritize, and where to move resources. The forecast predicted a 28% chain snatching spike from festival season. This transforms a police leader from reactive responder to strategic commander — backed by data, not intuition."

### Challenge 1 Requirements Demonstrated
| Requirement | How |
|-------------|-----|
| Req 1: Conversational Intelligence | Natural language strategic query |
| Req 3: Crime Pattern Analysis | District-wide trend analysis, hotspot migration, temporal patterns |
| Req 8: Crime Forecasting | Multi-category Prophet forecasts with seasonal context |
| Req 4: Sociological Insights | Demographic correlations, festival/seasonal context |
| Req 2: Criminal Network Analysis | Top network threat assessment |
| Req 6: Decision Support | Resource allocation recommendations |
| Req 10: RBAC | SP-level access to district-wide data; lower roles see only their jurisdiction |
| Req 9: Explainable AI | All trends cited to data, forecasts show confidence bands |

---

## Requirements Coverage Matrix

| Requirement | Scenarios Covering | Primary Demo |
|-------------|-------------------|--------------|
| **Req 1:** Conversational Intelligence | 1, 2, 3, 4, 5, 7, 8, 9, 10 | All scenarios |
| **Req 2:** Criminal Network Analysis | 1, 3, 6, 7, 8, 9, 10 | Scenario 8 (Drug Network) |
| **Req 3:** Crime Pattern Analysis | 1, 2, 4, 5, 7, 8, 10 | Scenario 4 (Hotspot Forecast) |
| **Req 4:** Sociological Insights | 4, 10 | Scenario 10 (Strategic Briefing) |
| **Req 5:** Offender Profiling | 1, 2, 5, 7, 8 | Scenario 2 (Cybercrime Repeat Offender) |
| **Req 6:** Decision Support | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | Scenario 5 (Hypothesis) |
| **Req 7:** Financial Crime Detection | 3, 6, 8 | Scenario 3 (UPI Money Trail) |
| **Req 8:** Crime Forecasting | 2, 4, 5, 6, 10 | Scenario 4 (Hotspot Forecast) |
| **Req 9:** Explainable AI | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | All scenarios |
| **Req 10:** RBAC | 6, 9, 10 | Scenario 10 (Strategic Briefing) |

**Coverage:** All 10 requirements demonstrated across multiple scenarios. Every requirement has at least 2 covering scenarios.

---

## Demo Script Order

### Recommended Sequence (Maximum Judge Impact)

The demo is structured as a **single narrative arc**: from a single crime → investigation depth → proactive intelligence → strategic command.

#### Opening (30 seconds)
> "InvestigateAI transforms Karnataka State Police from reactive responders into proactive intelligence-led investigators. Let me show you how one natural language question unlocks insights that would take weeks of manual work."

---

#### Act 1: "The Power of One Question" (5 minutes)

| Order | Scenario | Time | Why First |
|-------|----------|------|-----------|
| 1 | **Scenario 3: UPI Money Trail** | 2.5 min | Visual WOW factor — Sankey diagram is immediately impressive; judges see ₹12.3L traced in seconds |
| 2 | **Scenario 1: Vehicle Theft Ring** | 2.5 min | Shows network discovery — 12 FIRs connected through shared IMEIs; demonstrates cross-station intelligence |

**Transition:** *"Those were individual investigations. But what if the system finds connections the officer didn't even ask about?"*

---

#### Act 2: "The System Thinks Ahead" (5 minutes)

| Order | Scenario | Time | Why Here |
|-------|----------|------|----------|
| 3 | **Scenario 6: Proactive Alert** | 2 min | System-initiated intelligence — nobody asked, but the system detected the connection |
| 4 | **Scenario 5: Hypothesis Testing** | 3 min | Shows AI doesn't just confirm bias — it provides structured evidence FOR and AGAINST |

**Transition:** *"From reactive investigations to proactive prevention — let me show you how this transforms strategic policing."*

---

#### Act 3: "Strategic Command" (4 minutes)

| Order | Scenario | Time | Why Closing |
|-------|----------|------|-------------|
| 5 | **Scenario 4: Hotspot Forecast** | 2 min | Predictive policing — deploy before crime happens |
| 6 | **Scenario 10: Strategic Briefing** | 2 min | Grand finale — entire district intelligence in one query; shows SP-level power |

**Transition:** *"This is what intelligence-led policing looks like — from a single FIR to district-wide command, all through conversation."*

---

#### Closing (30 seconds)
> "Every fact cited. Every prediction explained. Every officer — from IO to SP — gets intelligence at their level. Zero cost beyond Catalyst credits. Built entirely on open-source AI."

---

### Timing Summary

| Segment | Duration |
|---------|----------|
| Opening | 0:30 |
| Scenario 3 (UPI Trail) | 2:30 |
| Scenario 1 (Vehicle Ring) | 2:30 |
| Transition | 0:15 |
| Scenario 6 (Proactive Alert) | 2:00 |
| Scenario 5 (Hypothesis) | 3:00 |
| Transition | 0:15 |
| Scenario 4 (Hotspot Forecast) | 2:00 |
| Scenario 10 (Strategic Briefing) | 2:00 |
| Closing | 0:30 |
| **TOTAL** | **15:30** |

**Buffer:** Can cut Scenario 1 to 2 min or skip transitions to hit 13 minutes if time is tight.

---

### Scenarios Held in Reserve (Not in Primary Demo)

| Scenario | When to Show | Use Case |
|----------|-------------|----------|
| Scenario 2 (Cybercrime Profiling) | If judges ask about offender profiling | Deep behavioral analysis showcase |
| Scenario 7 (Entity Resolution) | If judges ask about data quality | Shows system handles messy real-world data |
| Scenario 8 (Drug Network) | If judges ask about graph analysis depth | Most complex network analysis |
| Scenario 9 (Investigation Handover) | If judges ask about practical police needs | Solves real institutional problem |

---

### Fallback Strategy

| Risk | Mitigation |
|------|-----------|
| Live demo fails (network/API) | Pre-recorded video of all 6 primary scenarios (12 min, narrated) |
| Single scenario fails | Skip to next; each scenario is independent |
| LLM rate limit hit | Pre-cached responses for demo queries; deterministic engines still work |
| Neo4j cold start | Warm up 10 min before demo; cron ping keeps alive |
| Judge asks unexpected query | Switch to reserve scenario closest to their question; analyst handles live |

### Pre-Demo Checklist

- [ ] Neo4j warmed up (cron ping verified active)
- [ ] All 10 synthetic FIR datasets loaded and verified
- [ ] Demo user accounts created (IO, Analyst, DCP, SP) with correct RBAC
- [ ] Pre-computed intelligence cards refreshed
- [ ] Fallback video tested on presentation laptop
- [ ] SSE streaming verified on demo network
- [ ] Prophet models trained on synthetic data
- [ ] Graph algorithms pre-run (PageRank, Louvain, Betweenness)
- [ ] Sankey/timeline/map visualizations verified rendering correctly
- [ ] Audio pre-recorded for voice input demo (if included)

---

*End of Investigation Scenarios Document*
