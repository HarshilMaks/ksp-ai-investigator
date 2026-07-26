"""Typed Pydantic contracts for the internal T01–T23 registry.

These models validate tool boundaries only. They do not execute SQL, Cypher, model
calls, notifications, or other side effects. Unknown fields are rejected so a
planner cannot smuggle an unrestricted query through a typed tool.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ToolId = Literal[
    "T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10",
    "T11", "T12", "T13", "T14", "T15", "T16", "T17", "T18", "T19", "T20",
    "T21", "T22", "T23",
]


class RegistryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ToolCall(RegistryModel):
    tool_id: ToolId
    tool_name: str = Field(min_length=2, max_length=80)
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout_ms: int = Field(default=30_000, ge=100, le=300_000)
    retry_count: int = Field(default=2, ge=0, le=3)
    cache_key: str | None = Field(default=None, min_length=1, max_length=256)


class Citation(RegistryModel):
    source_type: Literal["FIR", "entity", "relationship", "computation", "investigation", "card"]
    source_id: str = Field(min_length=1, max_length=256)
    locator: str | None = Field(default=None, max_length=512)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ToolOutput(RegistryModel):
    tool_id: ToolId
    status: Literal["ok", "partial", "empty", "failed"] = "ok"
    data: dict[str, Any] | list[dict[str, Any]] = Field(default_factory=dict)
    citations: list[Citation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SQLQueryParams(RegistryModel):
    table: Literal["firs", "accused", "victims", "arrests", "properties"]
    filters: dict[str, Any] = Field(default_factory=dict)
    columns: list[str] = Field(default_factory=lambda: ["*"] , min_length=1, max_length=100)
    limit: int = Field(default=100, ge=1, le=1000)
    order_by: str | None = Field(default=None, max_length=120)

    @field_validator("columns")
    @classmethod
    def validate_columns(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("columns cannot contain empty names")
        return values


class VectorSearchParams(RegistryModel):
    query_text: str = Field(min_length=1, max_length=4000)
    collection: Literal["fir_narratives", "mo_descriptions", "witness_statements"]
    top_k: int = Field(default=20, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    metadata_filter: dict[str, Any] | None = None


class GraphTraverseParams(RegistryModel):
    start_entity: str = Field(min_length=1, max_length=256)
    entity_type: Literal["Person", "FIR", "Location", "Phone", "Vehicle", "Account"]
    relationship_types: list[str] = Field(default_factory=lambda: ["*"] , min_length=1, max_length=20)
    max_hops: int = Field(default=2, ge=0, le=5)
    direction: Literal["outgoing", "incoming", "both"] = "both"
    return_paths: bool = True


class CommunityDetectParams(RegistryModel):
    subgraph_filter: str | None = Field(default=None, max_length=1000)
    algorithm: Literal["louvain", "label_propagation", "wcc"] = "louvain"
    relationship_weight: str | None = Field(default=None, max_length=80)
    min_community_size: int = Field(default=3, ge=2, le=1000)


class CentralityScoreParams(RegistryModel):
    entity_type: str = Field(min_length=1, max_length=80)
    algorithm: Literal["pagerank", "betweenness", "degree", "closeness"] = "pagerank"
    subgraph_filter: str | None = Field(default=None, max_length=1000)
    top_k: int = Field(default=20, ge=1, le=100)
    damping_factor: float = Field(default=0.85, ge=0.0, le=1.0)


class ShortestPathParams(RegistryModel):
    source_entity: str = Field(min_length=1, max_length=256)
    target_entity: str = Field(min_length=1, max_length=256)
    relationship_types: list[str] = Field(default_factory=lambda: ["*"] , min_length=1, max_length=20)
    max_depth: int = Field(default=6, ge=0, le=10)
    algorithm: Literal["dijkstra", "bfs", "a_star"] = "dijkstra"
    weight_property: str | None = Field(default=None, max_length=80)


class EntityResolveParams(RegistryModel):
    name: str = Field(min_length=1, max_length=500)
    entity_type: Literal["person", "location", "phone", "vehicle"]
    methods: list[Literal["fuzzy", "phonetic", "alias_table", "ml_embedding"]] = Field(
        default_factory=lambda: ["fuzzy", "phonetic"], min_length=1, max_length=4
    )
    threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    include_kannada: bool = True


class PatternMatchParams(RegistryModel):
    crime_category: str | None = Field(default=None, max_length=100)
    time_window_days: int = Field(default=365, ge=1, le=3650)
    min_cluster_size: int = Field(default=5, ge=2, le=1000)
    features: list[Literal["mo_vector", "location", "time_of_day", "target_type"]] = Field(
        min_length=1, max_length=4
    )
    algorithm: Literal["hdbscan", "dbscan", "kmeans"] = "hdbscan"


class TemporalAnalysisParams(RegistryModel):
    metric: str = Field(min_length=1, max_length=100)
    group_by: str | None = Field(default=None, max_length=100)
    granularity: Literal["daily", "weekly", "monthly"] = "weekly"
    lookback_days: int = Field(default=730, ge=1, le=3650)
    forecast_days: int = Field(default=90, ge=0, le=730)
    detect_anomalies: bool = True


class HotspotDetectParams(RegistryModel):
    crime_category: str | None = Field(default=None, max_length=100)
    time_window_days: int = Field(default=90, ge=1, le=3650)
    h3_resolution: int = Field(default=8, ge=6, le=10)
    min_incidents: int = Field(default=5, ge=1, le=1000)
    return_geojson: bool = True


class FinancialTrailParams(RegistryModel):
    account_id: str | None = Field(default=None, min_length=1, max_length=256)
    upi_id: str | None = Field(default=None, min_length=1, max_length=256)
    phone_number: str | None = Field(default=None, min_length=1, max_length=32)
    direction: Literal["incoming", "outgoing", "both"] = "both"
    max_hops: int = Field(default=4, ge=0, le=8)
    min_amount: float = Field(default=0.0, ge=0.0)
    time_window_days: int = Field(default=90, ge=1, le=3650)
    flag_mules: bool = True

    @model_validator(mode="after")
    def require_subject(self) -> "FinancialTrailParams":
        if not any((self.account_id, self.upi_id, self.phone_number)):
            raise ValueError("one of account_id, upi_id, or phone_number is required")
        return self


class OffenderProfileParams(RegistryModel):
    person_id: str | None = Field(default=None, min_length=1, max_length=256)
    name: str | None = Field(default=None, min_length=1, max_length=500)
    include_sections: list[Literal[
        "risk_score", "criminal_history", "associates", "mo_pattern", "escalation", "locations", "financial"
    ]] = Field(default_factory=lambda: ["risk_score", "criminal_history", "associates"], min_length=1)

    @model_validator(mode="after")
    def require_subject(self) -> "OffenderProfileParams":
        if not self.person_id and not self.name:
            raise ValueError("person_id or name is required")
        return self


class SimilarCasesParams(RegistryModel):
    reference_fir_id: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None, min_length=1, max_length=4000)
    similarity_method: Literal["vector", "structural", "hybrid"] = "hybrid"
    crime_category_filter: str | None = Field(default=None, max_length=100)
    top_k: int = Field(default=10, ge=1, le=100)
    min_similarity: float = Field(default=0.70, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def require_reference(self) -> "SimilarCasesParams":
        if not self.reference_fir_id and not self.description:
            raise ValueError("reference_fir_id or description is required")
        return self


class TimelineBuildParams(RegistryModel):
    entity_id: str = Field(min_length=1, max_length=256)
    entity_type: str = Field(min_length=1, max_length=80)
    time_range_days: int = Field(default=365, ge=1, le=3650)
    include_events: list[Literal[
        "firs", "arrests", "court_dates", "bail", "transactions", "sightings", "associates_activity"
    ]] = Field(default_factory=lambda: ["firs", "arrests", "court_dates"], min_length=1)
    format: Literal["json", "markdown", "vis_timeline"] = "json"


class LeadGenerateParams(RegistryModel):
    evidence_collected: list[str] = Field(min_length=1, max_length=500)
    hypotheses: list[str] = Field(default_factory=list, max_length=100)
    investigation_goal: str = Field(min_length=1, max_length=2000)
    max_leads: int = Field(default=10, ge=1, le=100)
    include_rationale: bool = True


class CaseSummarizeParams(RegistryModel):
    fir_ids: list[str] = Field(min_length=1, max_length=100)
    include_sections: list[Literal[
        "overview", "key_findings", "evidence", "timeline", "connections", "risk_assessment", "recommendations"
    ]] = Field(default_factory=lambda: ["overview", "key_findings", "evidence", "recommendations"], min_length=1)
    max_words: int = Field(default=500, ge=50, le=5000)
    language: Literal["en", "kn"] = "en"
    cite_sources: bool = True


class ForecastCrimeParams(RegistryModel):
    district: str | None = Field(default=None, max_length=100)
    crime_category: str | None = Field(default=None, max_length=100)
    forecast_horizon_days: int = Field(default=90, ge=1, le=730)
    confidence_interval: float = Field(default=0.95, gt=0.0, lt=1.0)
    include_components: bool = True


class DemographicCorrelateParams(RegistryModel):
    crime_metric: str = Field(min_length=1, max_length=100)
    indicators: list[str] = Field(min_length=1, max_length=50)
    geography_level: Literal["district", "subdivision", "station"] = "district"
    method: Literal["pearson", "spearman", "mutual_info"] = "spearman"


class TranslateParams(RegistryModel):
    text: str = Field(min_length=1, max_length=20_000)
    source_lang: Literal["en", "kn"] = "en"
    target_lang: Literal["en", "kn"] = "kn"
    model: str = Field(default="indictrans2-onnx", min_length=1, max_length=100)
    preserve_entities: bool = True

    @model_validator(mode="after")
    def languages_must_differ(self) -> "TranslateParams":
        if self.source_lang == self.target_lang:
            raise ValueError("source_lang and target_lang must differ")
        return self


class ExplainReasoningParams(RegistryModel):
    conclusion: str = Field(min_length=1, max_length=4000)
    evidence_chain: list[str] = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)
    alternative_explanations: list[str] = Field(default_factory=list, max_length=50)
    format: Literal["structured", "narrative", "bullet"] = "structured"


class GenerateReportParams(RegistryModel):
    report_type: Literal["investigation", "intelligence", "briefing", "alert"]
    template: str = Field(default="default", min_length=1, max_length=100)
    sections: list[str] = Field(min_length=1, max_length=100)
    format: Literal["pdf", "html", "markdown"] = "pdf"
    language: Literal["en", "kn"] = "en"
    include_charts: bool = True
    classification: Literal["open", "restricted", "confidential"] = "restricted"


class PinEvidenceParams(RegistryModel):
    investigation_id: str = Field(min_length=1, max_length=256)
    evidence_type: Literal["fir", "person", "connection", "pattern", "financial", "location"]
    evidence_id: str = Field(min_length=1, max_length=256)
    note: str | None = Field(default=None, max_length=2000)
    priority: Literal["critical", "high", "medium", "low"] = "medium"


class AlertCreateParams(RegistryModel):
    alert_type: Literal["new_fir_match", "entity_activity", "pattern_trigger", "threshold_breach"]
    condition: dict[str, Any] = Field(min_length=1)
    notify_channels: list[Literal["app", "sms", "email"]] = Field(default_factory=lambda: ["app"], min_length=1)
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    expires_days: int = Field(default=30, ge=1, le=365)
    investigation_id: str | None = Field(default=None, max_length=256)


class RetrievalOutput(ToolOutput):
    data: list[dict[str, Any]] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class GraphOutput(ToolOutput):
    data: dict[str, Any] = Field(default_factory=dict)
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    paths: list[list[str]] = Field(default_factory=list)


class AnalysisOutput(ToolOutput):
    data: dict[str, Any] = Field(default_factory=dict)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    uncertainty: dict[str, Any] = Field(default_factory=dict)


class CommunicationOutput(ToolOutput):
    data: dict[str, Any] = Field(default_factory=dict)
    text: str | None = None


class ReportOutput(ToolOutput):
    data: dict[str, Any] = Field(default_factory=dict)
    artifact_id: str | None = None
    content_type: str | None = None


class EvidenceOutput(ToolOutput):
    data: dict[str, Any] = Field(default_factory=dict)
    evidence_id: str | None = None
    investigation_id: str | None = None


class AlertOutput(ToolOutput):
    data: dict[str, Any] = Field(default_factory=dict)
    alert_id: str | None = None
