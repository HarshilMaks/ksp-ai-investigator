# KSP InvestigateAI — Investigation Ontology
> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24


> The semantic layer that models every noun (entity), verb (action), relationship, rule, and permission in the crime investigation domain.

---

## Philosophy: Ontology-First Architecture

Palantir Gotham's core insight: **build the ontology FIRST**, then let the orchestrator and typed engines operate on the governed layer. Reasoning stages never touch raw data directly — typed tools query governed ontology projections. The ontology IS the world model.

```
┌─────────────────────────────────────────────────────────┐
│           ORCHESTRATOR + REASONING STAGES              │
│       (Planner? / Reasoner / Reporter)                  │
├─────────────────────────────────────────────────────────┤
│                 ONTOLOGY LAYER                           │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐            │
│  │ Entities │ │Relationships │ │  Rules   │            │
│  └──────────┘ └──────────────┘ └──────────┘            │
│  ┌──────────┐ ┌──────────────┐                         │
│  │ Actions  │ │ Permissions  │                         │
│  └──────────┘ └──────────────┘                         │
├─────────────────────────────────────────────────────────┤
│              DATA LAYER (Catalyst Data Store + Neo4j)             │
└─────────────────────────────────────────────────────────┘
```

---

## Demo governance and vocabulary

The canonical demo RBAC roles are SHO, IO, DCP, Analyst, and SP; a deeper production hierarchy is future scope. The MVP vocabulary is the entity/relationship subset used by the database schema; expanded entities and relationships below are optional future extensions. Risk, prediction, biometric, and similarity outputs are decision-support signals for human review, not determinations.

## Layer 1: Entity Layer (canonical MVP plus optional extensions)

Every noun in the investigation domain. Each entity has attributes, a canonical form, and resolution rules for deduplication.

| # | Entity Type | Canonical Form | Resolution Rule | Key Attributes |
|---|-------------|---------------|-----------------|----------------|
| 1 | **Person** | `UPPERCASE_NAME + DOB + FATHER_NAME` | Fuzzy name match (Jaro-Winkler > 0.88) + any shared identifier | name, dob, gender, father_name, address, aadhaar_hash, photo_embedding |
| 2 | **Phone** | `+91XXXXXXXXXX` (E.164) | Exact match on normalized number | number, imei, carrier, owner_entity_id |
| 3 | **Vehicle** | `KA-XX-XX-XXXX` (normalized plate) | Exact plate match OR chassis number match | registration_number, chassis_number, make, model, color, owner_entity_id |
| 4 | **UPI** | `lowercase@provider` | Exact match | upi_id, linked_phone, linked_bank_account |
| 5 | **BankAccount** | `IFSC:ACCOUNT_NUMBER` | Exact IFSC + account number | account_number, ifsc, bank_name, holder_name, account_type |
| 6 | **Location** | `lat,lng` (6 decimal precision) | Haversine distance < 50m OR exact address match | lat, lng, address, landmark, ps_jurisdiction, district |
| 7 | **CCTV** | `CAMERA_ID@LOCATION_ID` | Exact camera ID | camera_id, location_id, owner, type, resolution, coverage_angle |
| 8 | **Weapon** | `TYPE:MAKE:SERIAL` | Serial number match OR (type + make + caliber in same FIR) | type, make, caliber, serial_number, license_number |
| 9 | **Organization** | `UPPERCASE_NAME + DISTRICT` | Fuzzy name match (> 0.90) in same district | name, type, registration_number, address, district |
| 10 | **Document** | `DOC_TYPE:DOC_NUMBER` | Exact document number | doc_type, doc_number, issuer, holder_entity_id |
| 11 | **DigitalEvidence** | `SHA256_HASH` | Exact hash match | hash, file_type, source, collected_at, chain_of_custody |
| 12 | **Address** | `NORMALIZED_ADDR + PIN` | Geocoded location within 50m OR normalized string match > 0.92 | full_address, pin_code, district, ps_code, geocoded_lat, geocoded_lng |
| 13 | **FIR** | `PS_CODE/YEAR/FIR_NUMBER` | Exact match on composite key | fir_number, ps_code, year, crime_date, ipc_sections, status |
| 14 | **PoliceStation** | `PS_CODE` | Exact code match | ps_code, name, district, zone, lat, lng, sho_name |
| 15 | **CrimeCategory** | `CATEGORY:SUBTYPE` | Exact match | category, subtype, ipc_sections, severity_level |

### Entity Resolution Pipeline

```
Raw Extraction → Normalization → Canonical Form → Resolution Check → Merge/Create
     │                │                │                │               │
  NER/Regex      Format rules     Generate key     Search existing   Update graph
```

---

## Layer 2: Relationship Layer (20 Relationship Types)

Every verb/connection between entities. Each relationship has strength scoring, evidence backing, and discovery method.

| # | Relationship Type | Source → Target | Strength Formula | Discovery Method |
|---|------------------|-----------------|------------------|------------------|
| 1 | `ACCUSED_IN` | Person → FIR | 1.0 (explicit) | NER extraction from FIR narrative |
| 2 | `VICTIM_IN` | Person → FIR | 1.0 (explicit) | NER extraction from FIR narrative |
| 3 | `WITNESS_IN` | Person → FIR | 0.8 (explicit) | NER extraction from FIR narrative |
| 4 | `OWNS_PHONE` | Person → Phone | 0.9 (from record) | Extracted from FIR / telecom records |
| 5 | `OWNS_VEHICLE` | Person → Vehicle | 0.9 (from RTO) | RTO lookup / FIR narrative |
| 6 | `OWNS_ACCOUNT` | Person → BankAccount | 0.9 (from bank) | Bank records / UPI mapping |
| 7 | `LOCATED_AT` | FIR → Location | 1.0 (explicit) | Geocoding of FIR address |
| 8 | `CAPTURED_BY` | Person → CCTV | 0.7 (model confidence) | Face recognition / ANPR |
| 9 | `CALLED` | Phone → Phone | strength = min(call_count/10, 1.0) | CDR analysis |
| 10 | `TRANSACTED_WITH` | BankAccount → BankAccount | strength = min(txn_count/5, 1.0) | Financial records |
| 11 | `CO_ACCUSED_WITH` | Person → Person | strength = shared_fir_count / max_fir_count | **Computed**: shared ACCUSED_IN relationships |
| 12 | `SHARES_PHONE_WITH` | Person → Person | 0.85 (high signal) | **Computed**: multiple OWNS_PHONE to same Phone |
| 13 | `SHARES_VEHICLE_WITH` | Person → Person | 0.80 | **Computed**: multiple OWNS_VEHICLE to same Vehicle |
| 14 | `SHARES_UPI_WITH` | Person → Person | 0.85 | **Computed**: multiple persons linked to same UPI |
| 15 | `FINANCIAL_FLOW` | Person → Person | strength = min(total_amount/100000, 1.0) | **Computed**: chain of TRANSACTED_WITH |
| 16 | `TEMPORAL_PROXIMITY` | FIR → FIR | strength = 1.0 - (time_diff_hours / 72) | **Computed**: FIRs within 72h in same area |
| 17 | `SAME_MODUS_OPERANDI` | FIR → FIR | cosine_similarity(mo_vector) | **Computed**: MO embedding similarity > 0.82 |
| 18 | `BELONGS_TO_GANG` | Person → Organization | 0.9 (intelligence) | Intelligence reports / pattern analysis |
| 19 | `JURISDICTION_OF` | FIR → PoliceStation | 1.0 (explicit) | FIR registration data |
| 20 | `CATEGORIZED_AS` | FIR → CrimeCategory | 1.0 (explicit) | IPC section mapping |

### Strength Scoring

```
Final Strength = base_strength × recency_decay × evidence_multiplier

recency_decay = exp(-0.01 × days_since_last_evidence)
evidence_multiplier = min(evidence_count / 3, 1.5)
```

### Evidence Backing

Every relationship MUST reference at least one FIR ID as evidence. Relationships without evidence are marked `verified: false` and expire after 30 days.

---

## Layer 3: Action Layer (canonical T01-T23 typed registry)

### Engine ownership of actions

T01–T23 remain typed internal tools, not agents or public routes. Each tool delegates to a deterministic engine: SQL Retrieval (T01), Search/Ranking (T02/T13), Graph Intelligence (T03–T06), Pattern Analysis (T08/T09), Forecasting (T10/T17), Financial Analysis (T11), Behavioral Profiling (T12), Timeline (T14), Lead Ranking (T15), Reporter output (T16/T21/T23 where applicable), and Evidence/Explainability (T20/T22). The orchestrator controls execution; Planner/Reasoner/Reporter are the only LLM reasoning stages.

Every runtime action maps to one of the 23 internal T01-T23 typed tools in AGENTS.md. The ontology is a governed vocabulary implemented through Catalyst Data Store, Neo4j, and the typed registry; it is not a public query endpoint.

| # | Ontology action | Canonical registry tool | Input Ontology Objects | Output Ontology Objects | Side Effects |
|---|-----------------|------------------------|----------------------|------------------------|--------------|
| 1 | `search_firs` | T01 `sql_query` | query string, filters | FIR[] | audit_log entry |
| 2 | `semantic_search` | T02 `vector_search` | natural language query | FIR[] (ranked by similarity) | audit_log entry |
| 3 | `get_fir_details` | T01 `sql_query` | FIR | FIR (full) + Entity[] | audit_log entry |
| 4 | `extract_entities` | T07 `entity_resolve` (pipeline) | FIR narrative | Entity[] + Relationship[] | creates entities, links |
| 5 | `resolve_entity` | T07 `entity_resolve` | Entity (raw) | Entity (canonical) | merge if duplicate |
| 6 | `find_connections` | T03 `graph_traverse` | Entity | Relationship[] + Entity[] | none |
| 7 | `expand_network` | T03 `graph_traverse` | Entity, depth | Graph subgraph | none |
| 8 | `compute_co_accused` | T03 `graph_traverse` | Person | Person[] + strength | creates CO_ACCUSED_WITH |
| 9 | `detect_patterns` | T08 `pattern_match` | FIR[] | Pattern[] | creates intelligence_card |
| 10 | `predict_hotspots` | T10 `hotspot_detect` | Location, timerange | HotspotCard[] | creates intelligence_card |
| 11 | `score_offender` | T12 `offender_profile` | Person | OffenderProfile | creates intelligence_card |
| 12 | `trace_financial` | T11 `financial_trail` | BankAccount/UPI | FinancialTrail | creates intelligence_card |
| 13 | `find_similar_cases` | T13 `similar_cases` | FIR | SimilarCaseCard[] | creates intelligence_card |
| 14 | `generate_network_card` | T03/T05 graph tools | Person/Organization | NetworkIntelligenceCard | creates intelligence_card |
| 15 | `create_investigation` | future capability (workspace resource) | title, FIR | Investigation | audit_log entry |
| 16 | `add_evidence` | T22 `pin_evidence` | Investigation, Entity/FIR | InvestigationEvidence | audit_log entry |
| 17 | `build_timeline` | T14 `timeline_build` | Investigation | InvestigationTimeline[] | none |
| 18 | `generate_report` | T21 `generate_report` | Investigation | Document (PDF) | audit_log entry |
| 19 | `alert_similar_crime` | T23 `alert_create` | FIR | Alert → Users | notification |
| 20 | `escalate_case` | T23 `alert_create` | FIR, reason | FIR (updated priority) | notification to superior |
| 21 | `link_cases` | T13 `similar_cases` + T03 `graph_traverse` | FIR, FIR | Relationship (TEMPORAL_PROXIMITY/SAME_MO) | creates relationship |
| 22 | `verify_relationship` | T20 `explain_reasoning` | Relationship | Relationship (verified: true) | audit_log entry |
| 23 | `alert_create` | T23 `alert_create` | Alert payload | Alert → Users | Catalyst Signals event + audit_log entry |
---

## Layer 4: Rule Layer (Investigation Rules)

Automated rules that fire when ontology state changes.

### Escalation Rules

| Rule | Trigger | Action |
|------|---------|--------|
| `R-ESC-001` | FIR with IPC 302 (murder) | Auto-escalate to SP, set priority = CRITICAL |
| `R-ESC-002` | Person appears in > 5 FIRs within 90 days | Flag as serial offender, alert district IO |
| `R-ESC-003` | Financial flow > ₹10 lakhs across > 3 accounts | Escalate to Economic Offenses Wing |
| `R-ESC-004` | Gang network > 10 members with active FIRs | Escalate to Organized Crime Unit |
| `R-ESC-005` | FIR unresolved > 180 days with priority HIGH | Escalate to SP for review |

### Alert Rules

| Rule | Trigger | Recipients |
|------|---------|-----------|
| `R-ALT-001` | New FIR with MO similarity > 0.85 to unsolved case | Original IO |
| `R-ALT-002` | Known offender spotted in CCTV near crime scene | Jurisdiction SHO |
| `R-ALT-003` | Phone number from wanted person active in new FIR | Cybercrime cell |
| `R-ALT-004` | Vehicle from hit-and-run appears in new FIR | Traffic IO + original IO |
| `R-ALT-005` | Hotspot risk score exceeds threshold | Patrol units in area |

### Linking Rules

| Rule | Trigger | Action |
|------|---------|--------|
| `R-LNK-001` | Two FIRs share ≥ 2 entities (non-location) | Create TEMPORAL_PROXIMITY, suggest link |
| `R-LNK-002` | Two FIRs have MO similarity > 0.82 within same district | Create SAME_MODUS_OPERANDI |
| `R-LNK-003` | Phone used in FIR-A found in FIR-B | Create relationship, alert both IOs |
| `R-LNK-004` | Vehicle in FIR-A found in FIR-B | Create relationship, suggest joint investigation |
| `R-LNK-005` | Same accused in multiple open FIRs | Auto-link, generate NetworkIntelligenceCard |

---

## Layer 5: Permission Layer (RBAC on Ontology)

Role-Based Access Control mapped directly to ontology objects.

### Canonical demo roles

The demo exposes exactly five RBAC roles: **SHO, IO, DCP, Analyst, and SP**. Production hierarchy and counts are not part of the demo baseline.

### Expanded production hierarchy (future/optional)

The following hierarchy is retained as a future design reference and requires policy validation.

| Role | Description | Count (typical) |
|------|-------------|-----------------|
| `CONSTABLE` | Beat officer, patrol | ~50,000 |
| `SI` | Sub-Inspector, primary IO | ~10,000 |
| `INSPECTOR` | Station House Officer (SHO) | ~1,200 |
| `DSP` | Deputy SP, subdivision | ~200 |
| `SP` | Superintendent, district | ~35 |
| `DIG` | Deputy IG, range | ~10 |
| `IG` | Inspector General, zone | ~5 |
| `DGP` | Director General | 1 |
| `ANALYST` | Crime analyst (non-sworn) | ~100 |
| `ADMIN` | System administrator | ~5 |

### Expanded permission matrix (future/optional; demo uses the five roles above)

### Permission Matrix

| Ontology Object | CONSTABLE | SI | INSPECTOR | DSP+ | ANALYST |
|----------------|-----------|-----|-----------|------|---------|
| FIR (own PS) | READ | READ/WRITE | READ/WRITE/DELETE | ALL | READ |
| FIR (own district) | — | READ | READ | READ/WRITE | READ |
| FIR (other district) | — | — | — | READ | READ (anonymized) |
| Entity (Person) | READ (limited) | READ | READ | READ/WRITE | READ |
| Entity (Financial) | — | READ (own case) | READ | READ | READ |
| Relationships | READ | READ/CREATE | READ/CREATE/VERIFY | ALL | READ/CREATE |
| Intelligence Cards | — | READ (own cases) | READ (own PS) | READ (own district) | READ/CREATE |
| Investigations | — | OWN | OWN/TEAM | ALL | READ/SUPPORT |
| Audit Logs | — | — | — | READ (own) | — |
| System Config | — | — | — | — | — (ADMIN only) |

### Data Masking Rules

```
IF user.role < DSP AND entity.district != user.district:
    mask(person.name) → "P-XXXXX"
    mask(person.aadhaar) → HIDDEN
    mask(phone.number) → "+91XXXXX" + last4
    mask(bank_account) → HIDDEN
    
IF user.role == ANALYST:
    mask(person.name) → "SUBJECT-{hash[:8]}"
    mask(all_pii) → REDACTED
    allow(patterns, statistics, graphs)
```

---

## Intelligence Objects (Pre-Computed)

These are materialized views of the ontology — computed periodically and cached as `intelligence_cards`.

### 1. NetworkIntelligenceCard

```json
{
  "card_type": "NETWORK_INTELLIGENCE",
  "data": {
    "group_id": "uuid",
    "group_name": "Auto-detected or named",
    "members": [
      {"entity_id": "uuid", "name": "...", "role": "LEADER|MEMBER|BRIDGE|ASSOCIATE", "centrality_score": 0.92}
    ],
    "leaders": ["entity_id"],
    "bridges": ["entity_id"],  // nodes connecting sub-groups
    "crimes": [
      {"fir_id": "uuid", "category": "...", "date": "...", "members_involved": ["entity_id"]}
    ],
    "strength": 0.87,  // group cohesion (avg internal edge strength)
    "active_since": "2023-01-15",
    "last_activity": "2026-07-20",
    "territory": {"district": "...", "ps_codes": ["...", "..."]},
    "risk_level": "HIGH"
  }
}
```

### 2. OffenderProfile

```json
{
  "card_type": "OFFENDER_PROFILE",
  "data": {
    "entity_id": "uuid",
    "risk_score": 0.78,  // 0-1, composite
    "risk_components": {
      "recidivism_probability": 0.72,
      "violence_escalation": 0.45,
      "network_influence": 0.65,
      "flight_risk": 0.30
    },
    "modus_operandi": {
      "primary_method": "house-breaking",
      "tools_used": ["crowbar", "master-key"],
      "time_preference": "02:00-05:00",
      "target_preference": "residential, ground floor"
    },
    "temporal_pattern": {
      "active_days": ["friday", "saturday"],
      "active_hours": [2, 3, 4],
      "seasonal_peak": "october-december"
    },
    "geographic_pattern": {
      "primary_area": {"lat": 12.97, "lng": 77.59, "radius_km": 5},
      "secondary_areas": [],
      "mobility_score": 0.4
    },
    "escalation_history": ["petty_theft", "house_breaking", "armed_robbery"],
    "predicted_next": {"category": "armed_robbery", "confidence": 0.6, "timeframe_days": 90},
    "associated_network": "network_card_id"
  }
}
```

### 3. HotspotCard

```json
{
  "card_type": "HOTSPOT",
  "data": {
    "location": {"lat": 12.97, "lng": 77.59, "radius_m": 500},
    "area_name": "Majestic Bus Stand",
    "ps_code": "BNG-001",
    "category": "chain_snatching",
    "metrics": {
      "fir_count_30d": 12,
      "fir_count_90d": 34,
      "trend": "INCREASING",  // INCREASING | STABLE | DECREASING
      "trend_slope": 0.15,
      "yoy_change": "+28%"
    },
    "temporal_pattern": {
      "peak_hours": [17, 18, 19],
      "peak_days": ["monday", "friday"]
    },
    "forecast": {
      "next_7d_probability": 0.73,
      "next_30d_expected_count": 5
    },
    "risk_level": "HIGH",
    "recommended_patrol": {
      "beat_times": ["17:00-20:00"],
      "days": ["monday", "wednesday", "friday"],
      "unit_count": 2
    }
  }
}
```

### 4. FinancialTrail

```json
{
  "card_type": "FINANCIAL_TRAIL",
  "data": {
    "trail_id": "uuid",
    "source": {"entity_id": "uuid", "type": "BankAccount", "value": "SBIN0001234:9876543210"},
    "destination": {"entity_id": "uuid", "type": "UPI", "value": "mule99@paytm"},
    "hops": [
      {"from": "entity_id", "to": "entity_id", "amount": 50000, "timestamp": "...", "method": "UPI"},
      {"from": "entity_id", "to": "entity_id", "amount": 48000, "timestamp": "...", "method": "NEFT"}
    ],
    "total_amount": 250000,
    "hop_count": 4,
    "layering_pattern": "FAN_OUT",  // FAN_OUT | FAN_IN | CHAIN | ROUND_TRIP | STRUCTURING
    "velocity": "HIGH",  // time between first and last hop
    "suspicion_score": 0.91,
    "linked_firs": ["fir_id_1", "fir_id_2"],
    "mule_accounts": ["entity_id_3", "entity_id_4"]
  }
}
```

### 5. SimilarCaseCard

```json
{
  "card_type": "SIMILAR_CASE",
  "data": {
    "fir_a": "uuid",
    "fir_b": "uuid",
    "similarity_score": 0.89,
    "shared_entities": [
      {"entity_id": "uuid", "type": "Phone", "role_in_a": "accused_phone", "role_in_b": "suspect_phone"}
    ],
    "shared_modus_operandi": {
      "method_similarity": 0.92,
      "shared_keywords": ["knife", "two-wheeler", "gold-chain", "evening"],
      "time_similarity": 0.85,
      "location_proximity_km": 2.3
    },
    "recommendation": "LINK_INVESTIGATION",
    "confidence": "HIGH"
  }
}
```

---

## How the Orchestrator and Engines Query the Ontology vs Raw Data

### Ontology Queries (preferred; usage share is a target pending measurement)

The orchestrator routes typed tools to the **ontology layer** through structured queries:

```
# Orchestrator routes: "Who are the associates of suspect Ramesh Kumar?"
ONTOLOGY QUERY:
  MATCH (p:Person {canonical: "RAMESH KUMAR"})
  TRAVERSE [CO_ACCUSED_WITH | SHARES_PHONE_WITH | SHARES_VEHICLE_WITH] depth=2
  RETURN entities, relationships, strength
  FILTER strength > 0.5
  PERMISSION_CHECK user.role, user.district
```

The ontology handles:
- ✅ Entity resolution (finds canonical Ramesh Kumar even if FIR says "Ramesh K.")
- ✅ Permission filtering (masks data user shouldn't see)
- ✅ Strength scoring (returns only meaningful connections)
- ✅ Audit logging (records who queried what)
- ✅ Pre-computed intelligence (returns cached NetworkIntelligenceCard if available)

### Raw Data Queries (rare by design; usage share is a target pending measurement)

Only when:
1. **Semantic search** over narrative text (needs vector similarity on raw text)
2. **New entity extraction** from freshly filed FIR (needs raw narrative)
3. **Audit/compliance** requiring exact original text
4. **Bulk analytics** that need full table scans (analyst role only)

```
# Search/Ranking engine needs semantic search (falls through to raw)
RAW QUERY:
  SELECT fir_id, narrative_en, 1 - (narrative_vec <=> $query_vec) as similarity
  FROM firs
  WHERE crime_date > NOW() - INTERVAL '90 days'
  ORDER BY similarity DESC
  LIMIT 20
```

### Query Routing Logic

```python
def route_query(intent, user):
    if intent.type == "entity_lookup":
        return ontology.resolve_and_fetch(intent.entity)
    elif intent.type == "relationship_traversal":
        return ontology.traverse(intent.start, intent.depth, intent.filters)
    elif intent.type == "intelligence_card":
        card = ontology.get_cached_card(intent.card_type, intent.subject)
        if card and card.valid_until > now():
            return card
        else:
            return ontology.compute_card(intent.card_type, intent.subject)
    elif intent.type == "semantic_search":
        return tool_registry.invoke("T02", query_text=intent.query, authorization=user.permissions)
    elif intent.type == "narrative_extraction":
        return tool_registry.invoke("T01", fir_id=intent.fir_id, authorization=user.permissions)
    else:
        return tool_registry.invoke("T01", query=intent.query, authorization=user.permissions)
```

---

## Ontology Lifecycle

```
1. INGEST     → Raw FIR filed → Extract entities → Resolve → Add to ontology
2. ENRICH     → Compute relationships → Score strength → Fire rules
3. MATERIALIZE → Generate/refresh intelligence cards
4. SERVE      → Typed engines query ontology → Permission filter → Return
5. EVOLVE     → New entity types, relationships, rules added by admins
6. AUDIT      → Every mutation logged → Hash chain for tamper detection
```

---

*This ontology is the governed vocabulary for the demo system. Catalyst Data Store is authoritative for structured/vector records, Neo4j serves graph traversal, and typed tools enforce access; no reasoning stage accesses databases directly. Expanded entities, roles, and rules are future/optional.*
