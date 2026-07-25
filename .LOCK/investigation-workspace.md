# Investigation Workspace — Product Heart

> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24

---

## 1. Core Concept: Investigations, Not Conversations

The product is **NOT** a chat interface. It is a **persistent investigation workspace**.

```text
Other teams:
  Question → Answer → Done

This product:
  Investigation → Question → Evidence → Updated Investigation → Next Question → ...
  Officer closes case when ready. Nothing is lost.
```

Every interaction updates the investigation state. The conversation is one input method among many (pinning, hypothesis creation, manual evidence linking, officer notes).

The fundamental unit is the **Investigation**, not the message. Messages are ephemeral inputs; the investigation is the persistent, evolving artifact that accumulates knowledge over days, weeks, or months.

---

## 2. Investigation Lifecycle

### States

| State | Description | Transitions To |
|-------|-------------|----------------|
| **Created** | Officer creates or system suggests from proactive alerts | Active |
| **Active** | Collecting evidence, testing hypotheses, generating leads | Suspended, Closed |
| **Suspended** | Waiting for external input (CDR request, lab report, court order) | Active, Closed |
| **Closed** | Chargesheet filed, undetected, or cancelled | Archived |
| **Archived** | Read-only, searchable for precedent matching | — |

### Investigation Record

Every investigation has:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | System-generated unique identifier |
| `title` | string | Human-readable investigation name |
| `primary_firs` | FIR[] | One or more linked FIRs |
| `status` | enum | Created / Active / Suspended / Closed / Archived |
| `owner` | Officer | Primary investigating officer |
| `team` | Officer[] | Collaborating officers |
| `created_at` | timestamp | Investigation creation time |
| `updated_at` | timestamp | Last modification time |
| `closed_at` | timestamp | When investigation was closed (nullable) |

### State Transitions

- **Created → Active**: Officer begins work or system auto-activates on first evidence pin.
- **Active → Suspended**: Officer marks as waiting; system tracks what is pending.
- **Suspended → Active**: External input arrives; system can auto-reactivate with alert.
- **Active → Closed**: Officer files chargesheet, marks undetected, or cancels.
- **Closed → Archived**: Automatic after retention period; becomes read-only precedent.

---

## 3. Investigation Workspace Layout

The workspace is a 7-panel layout with an intelligence cards dock:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  Investigation: Whitefield UPI Fraud Ring   [Active] [SHO: Sharma]       │
├──────────┬──────────────┬──────────┬──────────┬─────────┬───────────────┤
│ CONVER-  │  EVIDENCE    │ TIMELINE │ NETWORK  │ LEADS   │ HYPOTHESIS    │
│ SATION   │  BOARD       │          │ GRAPH    │         │ PANEL         │
│          │              │          │          │         │               │
│ Chat +   │ Pinned items │ Events   │ Entities │ Ranked  │ Active hypos  │
│ Voice    │ with links   │ chrono   │ & links  │ actions │ For/Against   │
│ context  │ annotations  │ zoom     │ filter   │ status  │ confidence    │
└──────────┴──────────────┴──────────┴──────────┴─────────┴───────────────┘
│                          INTELLIGENCE CARDS                               │
│  [Offender Card] [Network Card] [Financial Trail] [Forecast] [Similar]   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Panel Descriptions

| Panel | Purpose | Updates When |
|-------|---------|--------------|
| **Conversation** | Chat + voice input with full investigation context | Officer sends message or voice input |
| **Evidence Board** | Pinned items with source links and annotations | Item pinned from any source |
| **Timeline** | Chronological event view with zoom/filter | Evidence with timestamps added |
| **Network Graph** | Entity-relationship visualization (force-directed) | New entities or relationships discovered |
| **Leads** | Ranked actionable items with status tracking | After each AI reasoning cycle |
| **Hypothesis Panel** | Active hypotheses with for/against/missing evidence | Evidence or hypothesis changes |
| **Intelligence Cards** | Generated artifact cards (dock/drawer) | Artifacts generated or updated |

### Synchronization Rule

**Every panel syncs with the investigation state.** Adding evidence in conversation updates the board, timeline, graph, and leads simultaneously. There is no "refresh" — the workspace is a live view of investigation state.

---

## 4. Persistent Case Memory

### What Persists Across Sessions

| Data | Persistence | Purpose |
|------|-------------|---------|
| Full conversation history | Permanent (with citations) | Context continuity |
| Pinned evidence items | Permanent | Investigation knowledge base |
| Active hypotheses + evaluation state | Permanent | Structured reasoning |
| Generated intelligence cards | Permanent (regenerable) | Analytical artifacts |
| Officer notes and annotations | Permanent | Human judgment record |
| Investigation timeline | Permanent (auto-updated) | Chronological understanding |
| Lead status | Permanent | Action tracking |
| Network graph state | Permanent (view state saved) | Visual analysis continuity |

### Session Continuity Experience

Officer returns tomorrow → AI knows exactly where the investigation stands.

The system can proactively say:

> "Since your last session, 2 new FIRs were filed that match your investigation criteria. Would you like to review them?"

> "The CDR report you requested 3 days ago has arrived. It confirms tower co-location for 2 of your 3 accused. Your hypothesis confidence has been updated to 84%."

There is **no cold start**. The investigation is alive whether the officer is looking at it or not.

---

## 5. Evidence Board

### Pinnable Entity Types

| Entity Type | Key Details | Example |
|-------------|-------------|---------|
| **FIRs** | Number, section, date, station, brief | FIR-2024-WF-1234 |
| **Persons** | Name, role (accused/victim/witness), photo, identifiers | Accused: Ramesh K. |
| **Vehicles** | Registration, make, model, color | KA-05-MN-4567 (White Innova) |
| **Phones/IMEI** | Number, IMEI, owner, tower history | 9845XXXXXX / IMEI:35267... |
| **UPI IDs** | VPA, linked bank, transaction volume | fraud.victim@paytm |
| **Bank Accounts** | Account number, bank, branch, holder | SBI Whitefield - 302010XXXXX |
| **Locations** | Address, lat/long, map pin, radius | 12.9716° N, 77.5946° E |
| **CCTV Records** | Location, timestamp, camera ID, clip link | Cam-07, 2024-03-15 02:34 AM |
| **Documents** | Type, source, date, summary | Post-mortem report, FSL report |
| **Intelligence Cards** | Generated card type, version | Offender Card v2 |
| **Custom Officer Notes** | Free-text with tags | "Informer says group meets at..." |

### Pinned Item Properties

Every pinned item:

- **Has a source** — which FIR, which engine, which query produced it
- **Can be annotated** — officer adds free-text notes to any item
- **Can be linked** — manual connections to other pinned items (officer draws the relationship)
- **Triggers AI re-reasoning** — when new items are added, the system re-evaluates all hypotheses and leads
- **Can be tagged** — `important` | `verify` | `suspicious` | `confirmed`

### Continuous Reasoning

AI continuously reasons over the board state:

> "You pinned 3 UPI IDs. I found they share a common beneficiary account not yet in your investigation. Would you like to add it?"

> "The vehicle you just pinned (KA-05-MN-4567) appears in 2 other active investigations. Flagging for your review."

This is not triggered by a question — it is triggered by **state change on the board**.

---

## 6. Hypothesis Management

### Hypothesis Structure

```text
Officer creates hypothesis:
  'These three robbery FIRs are committed by the same group.'

System evaluates:
  Supporting Evidence:
    ✓ Same vehicle spotted near 2 incidents (CCTV)
    ✓ Same phone IMEI active at all 3 locations
    ✓ Similar MO: night, residential, rear entry
  
  Contradicting Evidence:
    ✗ Different accused names in FIR 3
    ✗ Time gap (45 days) between FIR 1 and FIR 2

  Missing Evidence:
    □ CDR analysis for shared tower locations
    □ Financial link between accused

  Confidence: 72% (Medium-High)
  Status: Under Investigation
  Recommended Actions:
    1. Request CDR for all 3 accused
    2. Check bank accounts for common beneficiary
```

### Hypothesis Lifecycle

| Action | Actor | Description |
|--------|-------|-------------|
| **Create** | Officer | Officer states a hypothesis in natural language |
| **Suggest** | AI | System detects evidence pattern and proposes hypothesis |
| **Evaluate** | System | Automatically scores for/against/missing on creation and update |
| **Update** | System | Re-evaluates when new evidence arrives on the board |
| **Close** | Officer | Marks as confirmed / refuted / inconclusive |

### Confidence Scoring

| Range | Label | Meaning |
|-------|-------|---------|
| 0–25% | Low | Mostly contradicted or unsupported |
| 26–50% | Medium-Low | Some support, significant gaps |
| 51–75% | Medium-High | Good support, some contradictions or gaps |
| 76–100% | High | Strong support, minimal contradictions |

Confidence updates are **explainable** — every change shows what evidence moved the score and in which direction.

---

## 7. Proactive Intelligence

The system acts **WITHOUT being asked**:

| Trigger | System Action | Delivery |
|---------|---------------|----------|
| New FIR registered matching investigation entities | Alert officer | SSE push to workspace |
| New FIR matches MO pattern of active investigation | Suggest adding to investigation | Notification + evidence card |
| Entity in investigation appears in new context | Notify officer | Alert badge on entity |
| Forecast engine predicts crime spike in investigation area | Warn officer | Forecast card surfaced |
| Community detection finds new member matching network | Flag potential associate | Network graph highlight |
| Similar case resolved elsewhere | Surface for precedent | Similar Cases card |

### Implementation Architecture

```text
Catalyst Signals (CDC on FIR insert)
  → Compare against active investigation entities + MO patterns
    → Match found?
      → Push SSE alert to investigation workspace
      → Update investigation state (new_alerts queue)
      → Officer sees badge on next workspace visit
```

### Proactive vs. Reactive

- **Reactive**: Officer asks "Are there similar cases?" → System searches and responds.
- **Proactive**: System detects similar case filed 10 minutes ago → Pushes alert without being asked.

The proactive layer is what transforms this from a tool into a **partner**.

---

## 8. Artifacts Over Text

The AI produces **structured artifacts**, not just text responses:

| Artifact | Content | Trigger |
|----------|---------|---------|
| **Investigation Timeline** | Chronological events with entity links | Auto-generated, updated on evidence |
| **Criminal Network Graph** | Interactive force-directed graph | Updated when relationships discovered |
| **Offender Card** | Risk indicators, MO, history, associates | Generated per person entity |
| **Financial Trail** | Sankey/flow diagram of money movement | Generated when financial entities pinned |
| **Evidence Summary** | Structured brief with citations | On demand or auto at milestone |
| **Lead List** | Prioritized actions with confidence | Updated after each reasoning cycle |
| **Investigation Report** | Full PDF package | On demand (SmartBrowz/WeasyPrint) |
| **Hypothesis Evaluation** | Structured for/against/missing | Updated when hypothesis or evidence changes |
| **Similar Cases** | Matched past cases with outcomes | Computed on investigation creation |
| **Forecast Card** | Time/geo predictions with confidence bands | Pre-computed, surfaced when relevant |

### Artifact Properties

Every artifact:
- Is **versioned** — officer can see how it evolved
- Is **citeable** — every claim links back to source evidence
- Is **shareable** — can be exported or sent to other officers
- Is **interactive** — not static images, but explorable views
- Is **regenerable** — can be refreshed when new evidence arrives

### Why Artifacts Beat Text

Text answer: "There are 5 persons connected to this case..."
Artifact: Interactive network graph where officer can click nodes, expand relationships, filter by role, and discover connections visually.

The artifact **replaces** the text — it is the answer in a form that enables further investigation.

---

## 9. Entity Resolution

### The Problem

Police data is messy. The same real-world entity appears differently across FIRs:

- Same person, different spellings: `Harish Kumar` / `Harish K.` / `Hari Kumar`
- Same phone, different owners across FIRs
- Same vehicle, registration change
- Alias detection: `Raju` is also known as `Bullet Raju`

### Resolution Methods

| Method | Technique | Confidence | Use Case |
|--------|-----------|------------|----------|
| **Exact match** | Phone number, IMEI, vehicle reg, UPI ID, Aadhaar hash | 100% | Unique identifiers |
| **Fuzzy match** | Jaro-Winkler > 0.88 on names + shared identifier | 75–95% | Name variations |
| **Phonetic match** | Soundex/Metaphone for transliterated Kannada names | 60–85% | Transliteration variants |
| **Contextual** | Same FIR, same location, same time window | 50–80% | Co-occurrence |

### Resolution Output

- **Merge suggestions with confidence** — never auto-merge without officer approval for persons
- **Candidate clusters** shown in workspace — "These 3 records may be the same person"
- **Officer confirms or rejects** — explicit human decision
- **System learns from confirmations** — improves future matching

### Resolution Rules

| Entity Type | Auto-Merge Allowed? | Reason |
|-------------|---------------------|--------|
| Phone/IMEI | Yes (exact match) | Unique physical identifier |
| Vehicle Registration | Yes (exact match) | Unique legal identifier |
| UPI ID | Yes (exact match) | Unique digital identifier |
| Bank Account | Yes (exact match) | Unique financial identifier |
| Person | **Never auto-merge** | Legal implications; officer must confirm |
| Location | Yes (within 50m radius) | Geographic proximity |

---

## 10. Investigation Scenarios as Integration Tests

The 5 demo scenarios from DECISIONS.md are also **integration tests**. Each scenario must exercise:

1. **Full workspace activation** — all 7 panels populated and synced
2. **Evidence board population** — entities pinned from multiple sources
3. **Hypothesis creation and evaluation** — at least one hypothesis with for/against/missing
4. **Intelligence card generation** — relevant cards produced automatically
5. **Proactive alert firing** — system detects new relevant data and alerts
6. **Timeline auto-construction** — chronological view builds without manual input
7. **Leads ranked and actionable** — prioritized next steps with confidence scores

### Test Validation Criteria

| Criterion | Pass Condition |
|-----------|----------------|
| Workspace loads | All panels render within 2s |
| Evidence syncs | Pin in conversation → appears on board within 500ms |
| Hypothesis updates | New evidence → confidence recalculated within 1s |
| Cards generate | Offender card produced within 3s of person pin |
| Proactive alert | New matching FIR → alert within 5s |
| Timeline builds | Event with timestamp → timeline entry within 500ms |
| Leads update | New evidence → lead list re-ranked within 2s |

### Why Scenarios = Tests

If the demo scenario doesn't work end-to-end, the product doesn't work. There is no separate "demo mode" — the demo IS the product running on real (synthetic) data.

---

## 11. What Makes This Beat 200 Teams

| Dimension | Most teams | This product |
|-----------|------------|--------------|
| **Interaction** | Chat window | Persistent investigation workspace |
| **State** | Stateless Q&A | Living investigation with memory |
| **Output** | Text answers | Structured artifacts (timeline, graph, leads, cards) |
| **Intelligence** | Reactive (ask → get) | Proactive (system discovers, alerts) |
| **Decisions** | Suggestions | Prioritized, evidence-backed actionable leads |
| **Explainability** | "Source: FIR-123" | Visual reasoning graph + evidence chain + confidence |
| **Hypotheses** | None | Structured hypothesis testing with for/against/missing |
| **Continuity** | New session = fresh start | Officer returns, AI knows context |

### The Moat

1. **Investigation-native UX** — not chat bolted onto police data, but a workspace designed for how investigations actually work.
2. **Persistent state with proactive intelligence** — the system works even when the officer isn't looking.
3. **Hypothesis-driven reasoning** — structured analytical framework, not just Q&A.
4. **Entity resolution at scale** — the hardest data problem in police systems, solved with human-in-the-loop.
5. **Artifacts over text** — the output is investigation artifacts, not paragraphs.

### The Judge's 30-Second Test

When a judge evaluates this product, they will see:
- An officer opening an investigation that **remembers everything** from yesterday
- The system **proactively alerting** about a new FIR that matches the case
- A **network graph** that reveals a hidden connection the officer didn't see
- A **hypothesis** being updated in real-time as new evidence arrives
- **Leads** that tell the officer exactly what to do next, with confidence scores

This is not a chatbot. This is an **AI-powered investigation partner**.
