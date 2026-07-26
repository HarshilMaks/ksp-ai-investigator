"""Canonical internal T01–T23 registry manifest."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.domain.enums import AuditAction

from .schemas import (
    AlertCreateParams,
    AlertOutput,
    AnalysisOutput,
    CaseSummarizeParams,
    CentralityScoreParams,
    CommunityDetectParams,
    CommunicationOutput,
    DemographicCorrelateParams,
    EntityResolveParams,
    ExplainReasoningParams,
    EvidenceOutput,
    FinancialTrailParams,
    ForecastCrimeParams,
    GenerateReportParams,
    GraphOutput,
    GraphTraverseParams,
    HotspotDetectParams,
    LeadGenerateParams,
    OffenderProfileParams,
    PatternMatchParams,
    PinEvidenceParams,
    ReportOutput,
    RetrievalOutput,
    RegistryModel,
    ShortestPathParams,
    SimilarCasesParams,
    SQLQueryParams,
    TemporalAnalysisParams,
    TimelineBuildParams,
    ToolId,
    TranslateParams,
    VectorSearchParams,
    ToolOutput,
)

Stage = Literal["deterministic", "planner", "reasoner", "reporter"]


@dataclass(frozen=True)
class ToolSpec:
    tool_id: ToolId
    name: str
    description: str
    input_model: type[RegistryModel]
    output_model: type[ToolOutput]
    owner: str
    stage: Stage
    required_permissions: tuple[str, ...]
    audit_action: AuditAction
    citation_required: bool = True
    max_timeout_ms: int = 30_000
    public_route: bool = False


_READ = ("ontology:read",)
_WRITE = ("investigation:write",)

TOOL_SPECS: dict[str, ToolSpec] = {
    "T01": ToolSpec("T01", "sql_query", "Structured filters over authorized FIR records.", SQLQueryParams, RetrievalOutput, "sql_retrieval", "deterministic", _READ, AuditAction.SEARCH),
    "T02": ToolSpec("T02", "vector_search", "Semantic retrieval over authorized narrative collections.", VectorSearchParams, RetrievalOutput, "search_ranking", "deterministic", _READ, AuditAction.SEARCH),
    "T03": ToolSpec("T03", "graph_traverse", "Bounded graph traversal with relationship citations.", GraphTraverseParams, GraphOutput, "graph_intelligence", "deterministic", _READ, AuditAction.SEARCH),
    "T04": ToolSpec("T04", "community_detect", "Detect bounded graph communities for review.", CommunityDetectParams, AnalysisOutput, "graph_intelligence", "deterministic", _READ, AuditAction.SEARCH),
    "T05": ToolSpec("T05", "centrality_score", "Compute deterministic graph centrality signals.", CentralityScoreParams, AnalysisOutput, "graph_intelligence", "deterministic", _READ, AuditAction.SEARCH),
    "T06": ToolSpec("T06", "shortest_path", "Find a bounded, citable path between entities.", ShortestPathParams, GraphOutput, "graph_intelligence", "deterministic", _READ, AuditAction.SEARCH),
    "T07": ToolSpec("T07", "entity_resolve", "Resolve a supplied entity candidate against governed records.", EntityResolveParams, AnalysisOutput, "entity_resolution", "deterministic", _READ, AuditAction.QUERY_ONTOLOGY),
    "T08": ToolSpec("T08", "pattern_match", "Find deterministic modus-operandi and cluster signals.", PatternMatchParams, AnalysisOutput, "pattern_analysis", "deterministic", _READ, AuditAction.SEARCH),
    "T09": ToolSpec("T09", "temporal_analysis", "Compute temporal trends and anomaly signals.", TemporalAnalysisParams, AnalysisOutput, "pattern_analysis", "deterministic", _READ, AuditAction.SEARCH),
    "T10": ToolSpec("T10", "hotspot_detect", "Compute bounded spatial hotspot signals.", HotspotDetectParams, AnalysisOutput, "forecasting", "deterministic", _READ, AuditAction.SEARCH),
    "T11": ToolSpec("T11", "financial_trail", "Trace authorized financial relationships and mule indicators.", FinancialTrailParams, AnalysisOutput, "financial_analysis", "deterministic", _READ, AuditAction.SEARCH),
    "T12": ToolSpec("T12", "offender_profile", "Build deterministic review features for a person.", OffenderProfileParams, AnalysisOutput, "behavioral_profiling", "deterministic", _READ, AuditAction.SEARCH),
    "T13": ToolSpec("T13", "similar_cases", "Rank similar FIRs with method and citation metadata.", SimilarCasesParams, RetrievalOutput, "search_ranking", "deterministic", _READ, AuditAction.SEARCH),
    "T14": ToolSpec("T14", "timeline_build", "Assemble a cited chronological timeline.", TimelineBuildParams, AnalysisOutput, "timeline", "deterministic", _READ, AuditAction.SEARCH),
    "T15": ToolSpec("T15", "lead_generate", "Rank evidence-backed investigative leads for officer review.", LeadGenerateParams, AnalysisOutput, "lead_ranking", "deterministic", _READ, AuditAction.SEARCH),
    "T16": ToolSpec("T16", "case_summarize", "Produce a structured cited case summary.", CaseSummarizeParams, CommunicationOutput, "communication", "reporter", _READ, AuditAction.VIEW, max_timeout_ms=60_000),
    "T17": ToolSpec("T17", "forecast_crime", "Produce an uncertain, review-only crime forecast.", ForecastCrimeParams, AnalysisOutput, "forecasting", "deterministic", _READ, AuditAction.SEARCH, max_timeout_ms=60_000),
    "T18": ToolSpec("T18", "demographic_correlate", "Compute an explicitly non-causal demographic correlation.", DemographicCorrelateParams, AnalysisOutput, "social_analysis", "deterministic", _READ, AuditAction.SEARCH, max_timeout_ms=60_000),
    "T19": ToolSpec("T19", "translate", "Translate text while preserving governed entity terms.", TranslateParams, CommunicationOutput, "translation", "deterministic", _READ, AuditAction.VIEW, max_timeout_ms=60_000),
    "T20": ToolSpec("T20", "explain_reasoning", "Return structured evidence explanation without private chain-of-thought.", ExplainReasoningParams, AnalysisOutput, "evidence_explainability", "reasoner", _READ, AuditAction.QUERY_ONTOLOGY, max_timeout_ms=60_000),
    "T21": ToolSpec("T21", "generate_report", "Generate a cited, classified, human-reviewable report artifact.", GenerateReportParams, ReportOutput, "communication", "reporter", _READ, AuditAction.EXPORT, max_timeout_ms=300_000),
    "T22": ToolSpec("T22", "pin_evidence", "Pin an authorized artifact to an investigation evidence board.", PinEvidenceParams, EvidenceOutput, "investigation_state", "deterministic", _WRITE, AuditAction.ADD_EVIDENCE),
    "T23": ToolSpec("T23", "alert_create", "Create an authorized, expiring investigation alert.", AlertCreateParams, AlertOutput, "communication", "deterministic", _WRITE, AuditAction.CREATE, max_timeout_ms=60_000),
}

EXPECTED_TOOL_IDS = frozenset({f"T{index:02d}" for index in range(1, 24)})


def validate_manifest() -> None:
    """Fail closed if the registry is incomplete or has duplicate IDs."""

    actual = frozenset(TOOL_SPECS)
    if actual != EXPECTED_TOOL_IDS:
        missing = sorted(EXPECTED_TOOL_IDS - actual)
        extra = sorted(actual - EXPECTED_TOOL_IDS)
        raise RuntimeError(f"tool manifest mismatch: missing={missing}, extra={extra}")
    if len(TOOL_SPECS) != 23:
        raise RuntimeError("the internal registry must contain exactly 23 tools")


validate_manifest()


def get_tool_spec(tool_id: str) -> ToolSpec:
    try:
        return TOOL_SPECS[tool_id]
    except KeyError as exc:
        raise KeyError(f"unknown internal tool: {tool_id}") from exc
