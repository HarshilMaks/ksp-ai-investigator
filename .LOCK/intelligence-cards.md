# Intelligence Cards — Type Definitions

> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24

---

## Overview

Intelligence Cards are precomputed, structured artifacts that the GOTHAM system produces and surfaces in the investigation workspace. Each card represents a discrete unit of analytical output — a finding, prediction, profile, or recommendation — packaged for rapid officer consumption and action.

Cards are the primary interface between the AI engines and the human investigator. They are designed to be:
- **Self-contained** — each card carries its own context, confidence, and provenance
- **Actionable** — every card implies or recommends a next step
- **Auditable** — every card traces back to source data and reasoning
- **Perishable** — cards have freshness guarantees and auto-stale mechanisms

This document defines 15 Intelligence Card types.

---

## Card Type Definitions

---

### 1. Offender Profile Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | On-ingest (when new FIR names a known offender); Investigation-triggered (when officer opens offender view) |
| **Data Sources** | Behavioral Profiling Engine, CCTNS history, FIR corpus, Graph Intelligence Engine (associates) |
| **Update Frequency** | Re-computed on new FIR involving the offender; stale after 7 days without activity |
| **Confidence Methodology** | Composite score: criminal history completeness (0–1) × behavioral model confidence (0–1) × data recency factor (exponential decay, τ=90 days) |

**Schema (Key Fields):**

```json
{
  "card_type": "offender_profile",
  "entity_id": "string (offender UUID)",
  "risk_level": "enum: critical | high | medium | low",
  "risk_indicators": ["string"],
  "criminal_history_summary": {
    "total_firs": "integer",
    "conviction_count": "integer",
    "active_cases": "integer",
    "primary_ipc_sections": ["string"],
    "first_offense_date": "ISO-8601",
    "most_recent_offense_date": "ISO-8601"
  },
  "mo_signature": {
    "patterns": ["string"],
    "weapon_preference": "string | null",
    "target_type": "string",
    "time_preference": "string | null"
  },
  "escalation_pattern": {
    "trend": "enum: escalating | stable | de-escalating",
    "severity_trajectory": [{"date": "ISO-8601", "severity": "float"}],
    "predicted_next_severity": "float",
    "escalation_confidence": "float (0–1)"
  },
  "known_associates": [
    {"entity_id": "string", "relationship_type": "string", "strength": "float (0–1)"}
  ],
  "geographic_pattern": {
    "primary_districts": ["string"],
    "primary_stations": ["string"],
    "h3_hexagons": ["string (H3 index)"],
    "mobility_radius_km": "float"
  },
  "predicted_behavior": {
    "statement": "string (human-readable prediction)",
    "confidence": "float (0–1)",
    "basis": ["string (evidence references)"],
    "requires_human_review": true
  },
  "confidence_score": "float (0–1)",
  "generated_at": "ISO-8601",
  "stale_after": "ISO-8601",
  "provenance": {"engine": "behavioral_profiling", "model_version": "string", "data_snapshot": "ISO-8601"}
}
```

**Workspace Appearance:** Rendered as a full-width profile panel with risk badge (color-coded), collapsible sections for history/MO/associates/geography, and a prominent "Predicted Behavior" callout box marked with ⚠️ REQUIRES HUMAN REVIEW.

---

### 2. Criminal Network Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | On-demand (officer requests network expansion); Investigation-triggered (when 3+ entities in an investigation share connections) |
| **Data Sources** | Graph Intelligence Engine (Neo4j traversal), PageRank computation, Betweenness centrality, Community detection (Louvain) |
| **Update Frequency** | Re-computed when new edges added to subgraph; full recomputation on schedule (daily batch) |
| **Confidence Methodology** | Network confidence = min(edge_confidence) within community; stability score based on temporal edge persistence (edges present in >3 time windows = high stability) |

**Schema (Key Fields):**

```json
{
  "card_type": "criminal_network",
  "network_id": "string (community UUID)",
  "members": [
    {"entity_id": "string", "role": "enum: leader | bridge | peripheral | unknown", "centrality_score": "float"}
  ],
  "leaders": [{"entity_id": "string", "pagerank_score": "float"}],
  "bridge_nodes": [{"entity_id": "string", "betweenness_score": "float", "connects_communities": ["string"]}],
  "stability_score": "float (0–1)",
  "primary_crime_types": ["string (IPC sections)"],
  "geographic_span": {
    "districts": ["string"],
    "states": ["string"],
    "span_km": "float"
  },
  "temporal_span": {
    "first_activity": "ISO-8601",
    "last_activity": "ISO-8601",
    "active_duration_days": "integer"
  },
  "total_members": "integer",
  "total_edges": "integer",
  "density": "float",
  "confidence_score": "float (0–1)",
  "generated_at": "ISO-8601",
  "stale_after": "ISO-8601",
  "provenance": {"engine": "graph_intelligence", "algorithm": "string", "graph_snapshot": "ISO-8601"}
}
```

**Workspace Appearance:** Interactive Cytoscape.js force-directed graph visualization with node size proportional to centrality. Leaders highlighted in red, bridges in orange. Sidebar lists members ranked by role. Expandable to full-screen investigation board.

---

### 3. Financial Trail Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | On-demand (officer traces a transaction); Investigation-triggered (when flagged accounts appear in case) |
| **Data Sources** | Financial Analysis Engine, bank transaction feeds, UPI metadata, hawala intelligence |
| **Update Frequency** | Real-time for active investigations (streaming updates); batch daily for dormant trails |
| **Confidence Methodology** | Per-hop confidence based on transaction attribution certainty; overall trail confidence = product of hop confidences; layering indicator confidence from pattern-match score against known laundering templates |

**Schema (Key Fields):**

```json
{
  "card_type": "financial_trail",
  "trail_id": "string (UUID)",
  "investigation_id": "string | null",
  "source": {"account_id": "string", "entity_id": "string | null", "type": "string"},
  "destination": {"account_id": "string", "entity_id": "string | null", "type": "string"},
  "hops": [
    {
      "sequence": "integer",
      "from_account": "string",
      "to_account": "string",
      "amount": "float",
      "currency": "INR",
      "timestamp": "ISO-8601",
      "channel": "enum: UPI | NEFT | RTGS | cash | hawala | crypto",
      "confidence": "float (0–1)"
    }
  ],
  "total_amount": "float",
  "layering_indicators": {
    "rapid_movement": "boolean",
    "round_tripping": "boolean",
    "smurfing_detected": "boolean",
    "dormant_account_activation": "boolean",
    "pattern_match_score": "float (0–1)"
  },
  "mule_account_flags": [{"account_id": "string", "flag_reason": "string", "confidence": "float"}],
  "upi_rotation_patterns": {
    "detected": "boolean",
    "rotation_frequency_hours": "float | null",
    "vpa_count": "integer"
  },
  "confidence_score": "float (0–1)",
  "generated_at": "ISO-8601",
  "stale_after": "ISO-8601",
  "provenance": {"engine": "financial_analysis", "data_sources": ["string"], "analysis_window": "string"}
}
```

**Workspace Appearance:** Sankey diagram showing fund flow from source through intermediaries to destination. Suspicious hops highlighted in red. Mule accounts marked with warning icons. Expandable transaction table below visualization.

---

### 4. Crime Hotspot Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | Scheduled (daily batch computation for all active hexagons); On-demand (officer queries specific area) |
| **Data Sources** | Forecasting Engine, FIR geolocation data, historical crime density, temporal patterns, socioeconomic overlays |
| **Update Frequency** | Daily refresh at 00:30 IST; emergency recomputation on spike detection |
| **Confidence Methodology** | Forecast confidence from model prediction interval width; narrower interval = higher confidence. Calibrated via historical backtesting (expected 80% coverage at 80% CI). |

**Schema (Key Fields):**

```json
{
  "card_type": "crime_hotspot",
  "hexagon_id": "string (H3 resolution-8 index)",
  "district": "string",
  "station": "string",
  "crime_category": "string (IPC category)",
  "trend_direction": "enum: increasing | stable | decreasing",
  "trend_magnitude": "float (percent change vs baseline)",
  "risk_level": "enum: critical | high | medium | low",
  "forecast_confidence": "float (0–1)",
  "current_period_count": "integer",
  "baseline_count": "float (historical average for same period)",
  "comparison_to_baseline": "float (ratio)",
  "suggested_patrol_action": {
    "action": "string",
    "priority": "enum: immediate | high | routine",
    "optimal_time_window": "string",
    "resource_recommendation": "string"
  },
  "contributing_factors": ["string"],
  "confidence_score": "float (0–1)",
  "generated_at": "ISO-8601",
  "valid_until": "ISO-8601",
  "provenance": {"engine": "forecasting", "model": "string", "training_window": "string"}
}
```

**Workspace Appearance:** Map tile overlay on district map. Color intensity represents risk level. Clicking a hexagon expands the card with trend charts, patrol recommendations, and drill-down to contributing FIRs.

---

### 5. Similar Case Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | On-ingest (automatically for every new FIR, top-5 matches); Investigation-triggered (officer requests broader search) |
| **Data Sources** | Search/Ranking Engine (vector similarity on FIR embeddings), entity overlap computation, geographic proximity, temporal proximity |
| **Update Frequency** | Generated once on ingest; refreshed if matched case receives resolution update |
| **Confidence Methodology** | Composite similarity = weighted sum of dimension scores: entity_overlap (0.3) + mo_similarity (0.3) + geographic_proximity (0.2) + temporal_proximity (0.2). Threshold for surfacing: ≥ 0.65 |

**Schema (Key Fields):**

```json
{
  "card_type": "similar_case",
  "source_fir_id": "string",
  "matched_fir_id": "string",
  "overall_similarity": "float (0–1)",
  "similarity_dimensions": {
    "entity_overlap": {"score": "float", "shared_entities": ["string"]},
    "mo_similarity": {"score": "float", "matching_patterns": ["string"]},
    "geographic_proximity": {"score": "float", "distance_km": "float"},
    "temporal_proximity": {"score": "float", "gap_days": "integer"}
  },
  "matched_case_resolution": {
    "status": "enum: convicted | acquitted | pending | withdrawn | untraced",
    "resolution_date": "ISO-8601 | null",
    "key_evidence": ["string"],
    "investigating_officer": "string"
  },
  "applicable_precedent": {
    "exists": "boolean",
    "description": "string | null",
    "ipc_sections_applied": ["string"]
  },
  "confidence_score": "float (0–1)",
  "generated_at": "ISO-8601",
  "provenance": {"engine": "search_ranking", "embedding_model": "string", "index_snapshot": "ISO-8601"}
}
```

**Workspace Appearance:** Side-by-side comparison panel showing source FIR and matched FIR with highlighted matching dimensions. Resolution outcome prominently displayed with green (convicted) or grey (pending) badge. Linkable to open matched case.


---

### 6. Investigation Timeline Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | Investigation-triggered (created when investigation is opened); continuously updated as events occur |
| **Data Sources** | Timeline Engine, FIR records, arrest records, court dates, transaction timestamps, evidence submission logs, entity appearance logs |
| **Update Frequency** | Real-time append on new events; full reconstruction on-demand |
| **Confidence Methodology** | Per-event confidence based on source reliability (official record = 1.0, inferred from data = 0.5–0.9, officer-entered = 0.95). Overall timeline completeness score = events_found / estimated_total_events |

**Schema (Key Fields):**

```json
{
  "card_type": "investigation_timeline",
  "investigation_id": "string",
  "events": [
    {
      "event_id": "string",
      "timestamp": "ISO-8601",
      "event_type": "enum: fir_filed | entity_appeared | arrest | transaction | evidence_collected | court_date | bail | charge_sheet | other",
      "description": "string",
      "entities_involved": ["string (entity UUIDs)"],
      "source": "string",
      "confidence": "float (0–1)",
      "links": ["string (evidence/document IDs)"]
    }
  ],
  "total_events": "integer",
  "span": {"start": "ISO-8601", "end": "ISO-8601"},
  "gaps": [{"from": "ISO-8601", "to": "ISO-8601", "suspected_activity": "string | null"}],
  "completeness_score": "float (0–1)",
  "generated_at": "ISO-8601",
  "provenance": {"engine": "timeline", "sources_consulted": ["string"]}
}
```

**Workspace Appearance:** Horizontal scrollable timeline with event markers color-coded by type. Gaps highlighted with dashed lines. Hovering reveals event details. Filterable by event type and entity. Zoomable from day-level to year-level.

---

### 7. Hypothesis Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | Investigation-triggered (system proposes hypotheses on investigation creation); On-demand (officer or Reasoning Agent generates new hypothesis) |
| **Data Sources** | Evidence/Explainability Engine, Reasoning Agent, all evidence cards linked to the investigation |
| **Update Frequency** | Re-evaluated on every new evidence addition; confidence recalculated in real-time |
| **Confidence Methodology** | Bayesian-inspired: P(H|E) updated incrementally as evidence arrives. Supporting evidence increases confidence, contradicting evidence decreases it. Missing evidence penalizes proportionally to its expected availability. Final score = (supporting_weight − contradicting_weight) / (supporting_weight + contradicting_weight + missing_weight) normalized to 0–1 |

**Schema (Key Fields):**

```json
{
  "card_type": "hypothesis",
  "hypothesis_id": "string",
  "investigation_id": "string",
  "statement": "string (human-readable hypothesis)",
  "status": "enum: active | supported | refuted | inconclusive | superseded",
  "supporting_evidence": [
    {"evidence_id": "string", "description": "string", "weight": "float (0–1)", "date_added": "ISO-8601"}
  ],
  "contradicting_evidence": [
    {"evidence_id": "string", "description": "string", "weight": "float (0–1)", "date_added": "ISO-8601"}
  ],
  "missing_evidence": [
    {"description": "string", "importance": "float (0–1)", "suggested_action": "string"}
  ],
  "confidence_score": "float (0–1)",
  "confidence_trend": "enum: increasing | stable | decreasing",
  "recommended_actions": [
    {"action": "string", "expected_impact": "string", "priority": "enum: high | medium | low"}
  ],
  "generated_by": "enum: system | officer | reasoning_agent",
  "generated_at": "ISO-8601",
  "last_evaluated": "ISO-8601",
  "provenance": {"engine": "evidence_explainability + reasoning_agent", "reasoning_chain_id": "string"}
}
```

**Workspace Appearance:** Card with hypothesis statement as header, three-column evidence layout (supporting | contradicting | missing), confidence gauge (0–100%), and action buttons for "Add Evidence", "Mark Refuted", "Generate Sub-hypotheses". Status badge color-coded.

---

### 8. Evidence Summary Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | Investigation-triggered (created with investigation); continuously updated as evidence is linked |
| **Data Sources** | Evidence/Explainability Engine, all evidence repositories, officer submissions, automated evidence collection |
| **Update Frequency** | Real-time on evidence addition/modification; daily integrity check |
| **Confidence Methodology** | Per-evidence confidence based on source type (forensic = 0.95, documentary = 0.90, testimonial = 0.70, circumstantial = 0.50, AI-inferred = confidence from source engine). Overall evidence strength = weighted aggregate |

**Schema (Key Fields):**

```json
{
  "card_type": "evidence_summary",
  "investigation_id": "string",
  "total_evidence_items": "integer",
  "categories": {
    "forensic": [{"evidence_id": "string", "description": "string", "confidence": "float", "date_collected": "ISO-8601"}],
    "documentary": [{"evidence_id": "string", "description": "string", "confidence": "float", "date_collected": "ISO-8601"}],
    "testimonial": [{"evidence_id": "string", "description": "string", "confidence": "float", "date_collected": "ISO-8601"}],
    "digital": [{"evidence_id": "string", "description": "string", "confidence": "float", "date_collected": "ISO-8601"}],
    "circumstantial": [{"evidence_id": "string", "description": "string", "confidence": "float", "date_collected": "ISO-8601"}],
    "ai_inferred": [{"evidence_id": "string", "description": "string", "confidence": "float", "source_engine": "string", "date_collected": "ISO-8601"}]
  },
  "evidence_links": [
    {"from_evidence": "string", "to_evidence": "string", "relationship": "string"}
  ],
  "overall_evidence_strength": "float (0–1)",
  "gaps_identified": ["string"],
  "chain_of_custody_status": "enum: complete | partial | broken",
  "generated_at": "ISO-8601",
  "provenance": {"engine": "evidence_explainability", "sources_indexed": "integer"}
}
```

**Workspace Appearance:** Categorized accordion view with evidence items grouped by type. Each item shows confidence badge, provenance link, and date. Visual graph showing evidence interconnections. Gaps highlighted with red indicators and suggested collection actions.

---

### 9. Lead Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | Investigation-triggered (system generates initial leads on case creation); On new evidence (re-ranks and generates new leads); On-demand (officer requests lead generation) |
| **Data Sources** | Lead Ranking Engine, active investigation context, evidence gaps, entity graph, similar case resolutions |
| **Update Frequency** | Re-ranked on every evidence update; new leads generated daily for active investigations |
| **Confidence Methodology** | Lead confidence = P(action yields useful evidence) estimated from: similar case resolution patterns, evidence gap criticality, entity accessibility, and historical lead conversion rates for similar lead types |

**Schema (Key Fields):**

```json
{
  "card_type": "lead",
  "lead_id": "string",
  "investigation_id": "string",
  "action": "string (recommended investigative action)",
  "rationale": "string (why this lead matters)",
  "priority": "enum: critical | high | medium | low",
  "expected_evidence_gain": {
    "description": "string",
    "evidence_type": "string",
    "estimated_value": "float (0–1)"
  },
  "confidence": "float (0–1)",
  "related_entities": [{"entity_id": "string", "role_in_lead": "string"}],
  "status": "enum: pending | acted | dismissed | converted",
  "officer_assigned": "string | null",
  "due_date": "ISO-8601 | null",
  "outcome": "string | null",
  "generated_at": "ISO-8601",
  "acted_at": "ISO-8601 | null",
  "provenance": {"engine": "lead_ranking", "basis": ["string (evidence/hypothesis IDs)"]}
}
```

**Workspace Appearance:** Priority-sorted list with color-coded priority badges. Each lead shows action statement, confidence meter, and related entity chips. Action buttons: "Assign", "Act", "Dismiss with reason". Dismissed leads move to collapsed archive section.

---

### 10. Entity Resolution Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | On-ingest (when new entity has high similarity to existing entity); Scheduled (batch deduplication runs weekly) |
| **Data Sources** | Entity Resolution logic, name similarity (Jaro-Winkler, phonetic), address matching, biometric overlap (if available), co-occurrence in FIRs |
| **Update Frequency** | Generated on detection; expires after 30 days if not acted upon; re-generated if new supporting data arrives |
| **Confidence Methodology** | Weighted feature matching: name_similarity (0.25) + address_match (0.20) + age_proximity (0.15) + associate_overlap (0.15) + co_occurrence (0.15) + biometric (0.10). Merge threshold: ≥ 0.85 auto-suggest, ≥ 0.95 auto-merge with notification |

**Schema (Key Fields):**

```json
{
  "card_type": "entity_resolution",
  "resolution_id": "string",
  "entity_a": {"entity_id": "string", "name": "string", "source": "string"},
  "entity_b": {"entity_id": "string", "name": "string", "source": "string"},
  "match_dimensions": {
    "name_similarity": {"score": "float", "method": "string"},
    "address_match": {"score": "float", "details": "string"},
    "age_proximity": {"score": "float", "age_diff_years": "float"},
    "associate_overlap": {"score": "float", "shared_associates": "integer"},
    "co_occurrence": {"score": "float", "shared_firs": "integer"},
    "biometric": {"score": "float | null", "type": "string | null"}
  },
  "overall_confidence": "float (0–1)",
  "recommended_action": "enum: auto_merge | officer_review | no_action",
  "officer_action_required": "boolean",
  "merge_impact": {
    "firs_affected": "integer",
    "investigations_affected": "integer",
    "network_edges_merged": "integer"
  },
  "status": "enum: pending | merged | rejected | deferred",
  "generated_at": "ISO-8601",
  "expires_at": "ISO-8601",
  "provenance": {"engine": "entity_resolution", "algorithm_version": "string", "batch_id": "string | null"}
}
```

**Workspace Appearance:** Side-by-side entity comparison with matching fields highlighted in green, non-matching in red. Confidence gauge with breakdown by dimension. Action buttons: "Merge", "Not Same Person", "Defer — Need More Info". Impact statement showing what changes if merged.


---

### 11. Proactive Alert Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | On-ingest (new data matches active investigation criteria); Signal-triggered (streaming pattern detection) |
| **Data Sources** | Signals pipeline, investigation matching logic, entity watchlists, geographic triggers, temporal pattern alerts |
| **Update Frequency** | Real-time (generated as signals fire); auto-expires after 48 hours if not acknowledged |
| **Confidence Methodology** | Signal confidence × relevance to investigation. Signal confidence from source engine; relevance from entity/geographic/temporal overlap with active investigation parameters. Alert surfaced only if combined score ≥ 0.60 |

**Schema (Key Fields):**

```json
{
  "card_type": "proactive_alert",
  "alert_id": "string",
  "investigation_id": "string",
  "trigger": {
    "type": "enum: entity_activity | geographic_event | pattern_match | network_change | financial_movement",
    "source_signal": "string",
    "detected_at": "ISO-8601"
  },
  "what_changed": "string (human-readable description)",
  "why_it_matters": "string (relevance to investigation)",
  "new_data_reference": {"type": "string", "id": "string", "summary": "string"},
  "confidence": "float (0–1)",
  "urgency": "enum: immediate | high | routine",
  "suggested_action": "string",
  "status": "enum: new | acknowledged | acted | dismissed | expired",
  "acknowledged_by": "string | null",
  "acknowledged_at": "ISO-8601 | null",
  "generated_at": "ISO-8601",
  "expires_at": "ISO-8601",
  "provenance": {"engine": "signals_pipeline", "signal_type": "string", "matching_rule": "string"}
}
```

**Workspace Appearance:** Toast notification on arrival (dismissible). Persists in alert panel sorted by urgency. Red pulse animation for immediate urgency. Shows what changed, why it matters, and one-click action button. Expired alerts greyed out.

---

### 12. Sociological Insight Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | Scheduled (monthly batch analysis); On-demand (officer or policy analyst requests area analysis) |
| **Data Sources** | Pattern Analysis Engine, census data, socioeconomic indicators, FIR density data, educational/employment statistics, urbanization metrics |
| **Update Frequency** | Monthly refresh aligned with data availability; on-demand regeneration with current data |
| **Confidence Methodology** | Statistical significance (p-value < 0.05 required for surfacing); effect size (Cohen's d); correlation strength (Pearson r). Card explicitly states that correlation ≠ causation and flags confounding variables |

**Schema (Key Fields):**

```json
{
  "card_type": "sociological_insight",
  "insight_id": "string",
  "area": {"district": "string", "sub_district": "string | null", "h3_hexagons": ["string"]},
  "crime_type": "string (IPC category)",
  "correlation_factors": [
    {
      "factor": "string (e.g., unemployment_rate, population_density)",
      "correlation_coefficient": "float (-1 to 1)",
      "p_value": "float",
      "effect_size": "float",
      "direction": "enum: positive | negative"
    }
  ],
  "statistical_significance": "enum: high (p<0.01) | moderate (p<0.05) | low (p<0.10)",
  "trend": {
    "direction": "enum: strengthening | stable | weakening",
    "observation_period": "string"
  },
  "confounding_variables": ["string"],
  "qualification": "string (always includes: 'Correlation does not imply causation. This insight identifies statistical associations for investigative context, not causal claims.')",
  "policy_relevance": "string | null",
  "confidence_score": "float (0–1)",
  "generated_at": "ISO-8601",
  "valid_until": "ISO-8601",
  "provenance": {"engine": "pattern_analysis", "data_sources": ["string"], "methodology": "string"}
}
```

**Workspace Appearance:** Chart-centric card with scatter plot or correlation matrix visualization. Prominent yellow banner: "⚠️ CORRELATION ≠ CAUSATION". Factors listed with significance stars. Expandable methodology section. Available only to authorized roles (SHO+).

---

### 13. Forecast Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | Scheduled (daily for 30-day; weekly for 60/90-day); On-demand (officer requests specific district × category forecast) |
| **Data Sources** | Forecasting Engine, historical FIR time-series, seasonal decomposition, event calendar (festivals, elections), weather data |
| **Update Frequency** | 30-day: daily refresh; 60-day: weekly refresh; 90-day: weekly refresh. Emergency recomputation on major event |
| **Confidence Methodology** | Prediction interval width determines confidence band. Model uses ensemble (Prophet + LSTM + XGBoost); confidence = 1 − (interval_width / baseline_count). Backtesting calibration ensures stated 80% CI achieves ≥ 78% coverage |

**Schema (Key Fields):**

```json
{
  "card_type": "forecast",
  "forecast_id": "string",
  "district": "string",
  "station": "string | null",
  "crime_category": "string (IPC category)",
  "forecasts": [
    {
      "horizon_days": 30,
      "expected_count": "float",
      "confidence_band": {"lower": "float", "upper": "float", "confidence_level": 0.80},
      "trend_vs_baseline": "float (percent change)"
    },
    {
      "horizon_days": 60,
      "expected_count": "float",
      "confidence_band": {"lower": "float", "upper": "float", "confidence_level": 0.80},
      "trend_vs_baseline": "float (percent change)"
    },
    {
      "horizon_days": 90,
      "expected_count": "float",
      "confidence_band": {"lower": "float", "upper": "float", "confidence_level": 0.80},
      "trend_vs_baseline": "float (percent change)"
    }
  ],
  "contributing_factors": [
    {"factor": "string", "impact": "enum: increasing | decreasing", "magnitude": "float"}
  ],
  "historical_baseline": {
    "same_period_last_year": "float",
    "3_year_average": "float",
    "trend_direction": "enum: increasing | stable | decreasing"
  },
  "model_performance": {"mape": "float", "coverage_80ci": "float"},
  "confidence_score": "float (0–1)",
  "generated_at": "ISO-8601",
  "valid_until": "ISO-8601",
  "provenance": {"engine": "forecasting", "models_used": ["string"], "training_window": "string"}
}
```

**Workspace Appearance:** Time-series chart with historical data (solid line), forecast (dashed line), and confidence band (shaded area). Baseline comparison as dotted line. Contributing factors listed below with directional arrows. Drill-down to station-level available.

---

### 14. Case Summary Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | On-demand (officer requests brief); Scheduled (weekly auto-generation for all active investigations); Investigation-triggered (generated on investigation close) |
| **Data Sources** | Reporter Agent, all cards linked to investigation (timeline, hypotheses, evidence, leads, network), FIR text, officer notes |
| **Update Frequency** | Regenerated on-demand; auto-refreshed weekly for active cases; final version on case closure |
| **Confidence Methodology** | Summary confidence = completeness of source data × consistency of narrative. Flags sections where information is uncertain or contradictory. Overall investigation progress score based on evidence coverage and hypothesis resolution |

**Schema (Key Fields):**

```json
{
  "card_type": "case_summary",
  "investigation_id": "string",
  "summary_version": "integer",
  "key_facts": [
    {"fact": "string", "confidence": "float (0–1)", "source": "string"}
  ],
  "timeline_summary": {
    "start_date": "ISO-8601",
    "key_milestones": [{"date": "ISO-8601", "event": "string"}],
    "duration_days": "integer"
  },
  "network_summary": {
    "key_entities": [{"entity_id": "string", "role": "string"}],
    "total_entities": "integer",
    "network_card_id": "string | null"
  },
  "leads_summary": {
    "total_leads": "integer",
    "acted": "integer",
    "pending": "integer",
    "converted": "integer",
    "critical_pending": [{"lead_id": "string", "action": "string"}]
  },
  "hypothesis_status": [
    {"hypothesis_id": "string", "statement": "string", "status": "string", "confidence": "float"}
  ],
  "recommended_next_steps": [
    {"step": "string", "priority": "enum: critical | high | medium | low", "rationale": "string"}
  ],
  "investigation_progress": "float (0–1)",
  "narrative": "string (auto-generated prose summary, 500–1000 words)",
  "generated_at": "ISO-8601",
  "provenance": {"engine": "reporter_agent", "source_cards": ["string"], "generation_model": "string"}
}
```

**Workspace Appearance:** Document-style card with structured sections. Executive summary at top (2–3 sentences). Expandable sections for timeline, network, leads, hypotheses. "Export as PDF" and "Share with supervisor" buttons. Progress bar showing investigation completeness.

---

### 15. Reasoning Trace Card

| Attribute | Value |
|-----------|-------|
| **When Generated** | On-demand (officer requests explanation for any AI output); Auto-generated (attached to every Hypothesis Card and Lead Card) |
| **Data Sources** | Evidence/Explainability Engine, engine invocation logs, evidence retrieval records, inference chain |
| **Update Frequency** | Immutable once generated (represents reasoning at a point in time); new trace generated for updated conclusions |
| **Confidence Methodology** | Per-step confidence propagation: each step's output confidence ≤ min(input confidence, step model confidence). Final conclusion confidence = product of step confidences along critical path. Uncertainty accumulation explicitly shown |

**Schema (Key Fields):**

```json
{
  "card_type": "reasoning_trace",
  "trace_id": "string",
  "parent_card_id": "string (hypothesis/lead/alert card this explains)",
  "parent_card_type": "string",
  "question": "string (the question being answered or conclusion being explained)",
  "chain": [
    {
      "step": "integer",
      "action": "enum: query | retrieve | compute | infer | aggregate | rank",
      "engine_invoked": "string",
      "input": "string (what was asked of the engine)",
      "output_summary": "string (what was returned)",
      "evidence_found": [{"evidence_id": "string", "relevance": "float"}],
      "confidence_at_step": "float (0–1)",
      "duration_ms": "integer"
    }
  ],
  "inference_made": "string",
  "conclusion": "string",
  "conclusion_confidence": "float (0–1)",
  "uncertainty_factors": ["string (what could change the conclusion)"],
  "alternative_conclusions": [
    {"conclusion": "string", "confidence": "float", "why_not_chosen": "string"}
  ],
  "generated_at": "ISO-8601",
  "provenance": {"engine": "evidence_explainability", "trace_version": "string"}
}
```

**Workspace Appearance:** Visual flowchart/DAG showing Question → Engine nodes → Evidence nodes → Inference → Conclusion. Each node clickable for details. Confidence shown as progressively narrowing bar. Alternative paths shown as greyed branches. "Challenge this reasoning" button for officer feedback.


---

## Card Storage Architecture

### Storage Layers

Intelligence Cards are stored across three layers optimized for different access patterns:

| Layer | Technology | Purpose | Retention |
|-------|-----------|---------|-----------|
| **Hot Cache** | Catalyst Cache (Redis cluster) | Active cards for open investigations; sub-10ms read latency | Active cards + 7 days after last access |
| **Primary Store** | Stratus JSON (S3-compatible object store) | Canonical card storage; full JSON with versioning | Indefinite (lifecycle-managed) |
| **Metadata Index** | Data Store (PostgreSQL) | Card metadata for search, filtering, aggregation; no full payload | Indefinite |

### Storage Flow

```
Engine produces card
  → Write to Stratus JSON (canonical, versioned)
  → Index metadata in Data Store (card_id, type, investigation_id, generated_at, confidence, status)
  → Push to Catalyst Cache if card is for active investigation
  → Emit card_created event to event bus
```

### Versioning

- Every card update creates a new version in Stratus JSON (immutable append)
- Previous versions retained for audit trail
- Data Store tracks current_version pointer
- Catalyst Cache always holds latest version only

### Access Patterns

| Pattern | Path |
|---------|------|
| Single card by ID | Catalyst Cache (hit) → Stratus JSON (miss) |
| Cards for investigation | Data Store query → batch fetch from Catalyst/Stratus |
| Card search (type, date, confidence) | Data Store query |
| Historical card versions | Stratus JSON version listing |
| Card aggregation/analytics | Data Store aggregate queries |

---

## Workspace Rendering

### Rendering Architecture

All Intelligence Cards are rendered as **React 19 components organized by Feature-Sliced Design** in the Next.js 15 App Router investigation workspace. The rendering system follows a consistent pattern:

```
Card JSON → CardRenderer (type router) → Specific Card Component → Rendered UI
```

### Component Hierarchy

```
<InvestigationWorkspace>
  <CardGrid>
    <CardContainer card={card}>        // Handles: pin, expand, share, refresh
      <CardHeader />                   // Type icon, title, confidence badge, timestamps
      <CardBody type={card.type} />    // Type-specific visualization
      <CardFooter />                   // Provenance, actions, version info
    </CardContainer>
  </CardGrid>
  <CardDetailPanel />                  // Full-screen expanded view
</InvestigationWorkspace>
```

### Interaction Patterns

| Feature | Behavior |
|---------|----------|
| **Pinnable** | Officer pins critical cards to top of workspace; pinned cards persist across sessions |
| **Expandable** | Click to expand from summary view → full detail view with all schema fields |
| **Shareable** | Share card with team members or supervisors; generates read-only link with access control |
| **Refreshable** | Manual refresh triggers re-computation with latest data |
| **Linkable** | Cards cross-reference each other; clicking entity/evidence IDs navigates to related cards |
| **Annotatable** | Officers can add notes/comments to any card without modifying the AI-generated content |
| **Exportable** | Export as PDF, JSON, or include in generated reports |

### Confidence Visualization

All cards display confidence using a consistent visual language:
- **≥ 0.80**: Green badge, solid indicators
- **0.60–0.79**: Yellow badge, normal indicators
- **0.40–0.59**: Orange badge, dashed indicators, "Low Confidence" warning
- **< 0.40**: Red badge, dotted indicators, "Very Low Confidence — Verify Before Acting" warning

### Responsive Layout

- **Desktop (≥1200px)**: Multi-column card grid, side-by-side comparisons
- **Tablet (768–1199px)**: Two-column grid, stacked comparisons
- **Mobile (≤767px)**: Single-column, simplified card views (field officers in the field)

---

## Card Lifecycle

### States

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌───────────┐     ┌──────────────┐
│ CREATED  │ ──▶ │  ACTIVE  │ ──▶ │  STALE   │ ──▶ │ REFRESHED │ ──▶ │   ARCHIVED   │
└──────────┘     └──────────┘     └──────────┘     └───────────┘     └──────────────┘
                       │                │                                      ▲
                       │                └──── (no refresh triggered) ──────────┘
                       │
                       └──── (investigation closed) ──────────────────────────▶┘
```

### State Definitions

| State | Definition | Trigger to Next State |
|-------|-----------|----------------------|
| **Created** | Card generated, not yet delivered to workspace | Delivery to workspace → Active |
| **Active** | Card visible in workspace, within freshness window | Freshness window expires → Stale |
| **Stale** | Card past freshness window; visual indicator shown to officer | Engine re-computes → Refreshed; or TTL expires → Archived |
| **Refreshed** | Re-computed with latest data; replaces stale version | Returns to Active state |
| **Archived** | Investigation closed or card superseded; read-only, searchable | Terminal state (retained for audit) |

### Freshness Rules

| Card Type | Freshness Window | Stale Warning |
|-----------|-----------------|---------------|
| Offender Profile | 7 days | "Profile may not reflect recent activity" |
| Criminal Network | 24 hours | "Network structure may have changed" |
| Financial Trail | 6 hours (active investigation) | "New transactions may exist" |
| Crime Hotspot | 24 hours | "Forecast based on yesterday's data" |
| Similar Case | 30 days | "New cases may match" |
| Investigation Timeline | Real-time (never stale while active) | N/A |
| Hypothesis | Real-time (re-evaluated on evidence) | N/A |
| Evidence Summary | Real-time (append-only) | N/A |
| Lead | 24 hours | "Leads may need re-prioritization" |
| Entity Resolution | 30 days | "New data may affect match" |
| Proactive Alert | 48 hours | Auto-expires (not stale, just expired) |
| Sociological Insight | 30 days | "Monthly refresh pending" |
| Forecast | 24 hours (30-day) / 7 days (60/90-day) | "Forecast may not reflect latest trends" |
| Case Summary | 7 days | "Summary may be outdated" |
| Reasoning Trace | Never stale (immutable) | N/A |

### Archival Policy

- Cards for closed investigations: archived 30 days after closure
- Superseded cards: archived immediately (old version retained)
- Expired alerts: archived after 48 hours
- All archived cards searchable and retrievable for audit/legal purposes
- Retention: minimum 7 years (aligned with legal record requirements)

---

## Alignment with Challenge 1 Requirements

### Challenge 1 Context

KGID Challenge 1 requires demonstrating AI-augmented investigation capabilities across multiple scenarios. Intelligence Cards directly support each evaluation criterion:

### Requirement Mapping

| Challenge 1 Requirement | Supporting Cards | How Cards Satisfy Requirement |
|--------------------------|-----------------|-------------------------------|
| **Offender Profiling & Risk Assessment** | Offender Profile Card, Criminal Network Card | Structured risk indicators with explainable scoring; escalation prediction with human review gate |
| **Crime Pattern Detection** | Crime Hotspot Card, Forecast Card, Sociological Insight Card | Spatial-temporal patterns surfaced as actionable hexagon-level insights with patrol recommendations |
| **Link Analysis & Network Intelligence** | Criminal Network Card, Financial Trail Card, Entity Resolution Card | Graph-based community detection with centrality metrics; financial flow tracing; entity deduplication |
| **Investigation Support** | Hypothesis Card, Evidence Summary Card, Lead Card, Investigation Timeline Card | Structured analytical framework: hypotheses, evidence tracking, prioritized leads, chronological reconstruction |
| **Predictive Analytics** | Forecast Card, Crime Hotspot Card | 30/60/90-day forecasts with calibrated confidence bands; hotspot trend detection |
| **Case Similarity & Precedent** | Similar Case Card | Multi-dimensional similarity matching with resolution outcomes and applicable precedents |
| **Explainability & Transparency** | Reasoning Trace Card, all cards (confidence fields) | Every AI output traceable to source data and reasoning chain; confidence methodology documented per card |
| **Proactive Intelligence** | Proactive Alert Card, Lead Card | Real-time signal matching to active investigations; prioritized investigative recommendations |
| **Reporting & Summarization** | Case Summary Card | Auto-generated investigation briefs with structured sections and export capabilities |

### Evaluation Criteria Alignment

| Evaluation Criterion | Card System Response |
|---------------------|---------------------|
| **Accuracy** | Per-card confidence scores with documented methodology; calibrated prediction intervals |
| **Explainability** | Reasoning Trace Card attached to every inference; provenance on every card |
| **Actionability** | Every card implies or recommends next steps; Lead Card specifically ranks actions |
| **Timeliness** | Real-time cards for active investigations; defined freshness windows; proactive alerts |
| **Officer Trust** | Confidence visualization; human-in-the-loop for predictions; "Challenge this reasoning" feature |
| **Integration** | Cards consume from all engines; workspace renders unified view regardless of source |

### Demo Scenario Coverage

For each Challenge 1 demo scenario, the investigation workspace surfaces the relevant combination of cards:

1. **Serial Offender Identification**: Offender Profile + Criminal Network + Similar Case + Reasoning Trace
2. **Organized Crime Network**: Criminal Network + Financial Trail + Entity Resolution + Lead
3. **Crime Forecasting**: Forecast + Crime Hotspot + Sociological Insight + Proactive Alert
4. **Cold Case Resolution**: Similar Case + Hypothesis + Evidence Summary + Investigation Timeline
5. **Real-time Investigation**: Proactive Alert + Lead + Case Summary + Reasoning Trace

---

## Summary

The 15 Intelligence Card types form a complete analytical output layer for the GOTHAM system. They transform raw engine outputs into structured, confidence-rated, explainable artifacts that officers can consume, act upon, and trust. The card system directly addresses every Challenge 1 evaluation criterion while maintaining auditability, freshness guarantees, and human oversight requirements.

Total card types: **15**
Storage: **Stratus JSON (canonical) + Catalyst Cache (hot) + Data Store (metadata)**
Rendering: **Next.js 15/React 19 Feature-Sliced component library with consistent interaction patterns**
Lifecycle: **Created → Active → Stale → Refreshed → Archived**
Confidence: **Per-card methodology with visual language (green/yellow/orange/red)**
