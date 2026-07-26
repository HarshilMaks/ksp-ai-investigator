"""Typed intelligence-card payloads and immutable lifecycle records for P14.

Product cards are presentation/analytical artifacts. They are intentionally not
logical schema entities and carry source provenance back to those entities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CardType(str, Enum):
    OFFENDER_PROFILE = "offender_profile"
    CRIMINAL_NETWORK = "criminal_network"
    FINANCIAL_TRAIL = "financial_trail"
    CRIME_HOTSPOT = "crime_hotspot"
    SIMILAR_CASE = "similar_case"
    INVESTIGATION_TIMELINE = "investigation_timeline"
    HYPOTHESIS = "hypothesis"
    EVIDENCE_SUMMARY = "evidence_summary"
    LEAD = "lead"
    ENTITY_RESOLUTION = "entity_resolution"
    PROACTIVE_ALERT = "proactive_alert"
    SOCIOLOGICAL_INSIGHT = "sociological_insight"
    FORECAST = "forecast"
    CASE_SUMMARY = "case_summary"
    REASONING_TRACE = "reasoning_trace"


class CardStatus(str, Enum):
    ACTIVE = "active"
    STALE = "stale"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class CardModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    card_type: CardType
    requires_human_review: bool = True

    @field_validator(
        "confidence_score", "forecast_confidence", "confidence", "overall_confidence",
        "conclusion_confidence", "overall_similarity", "completeness_score", "investigation_progress", "density",
        check_fields=False,
    )
    @classmethod
    def bounded_score(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("card confidence and score fields must be between 0 and 1")
        return value


class OffenderProfileCard(CardModel):
    card_type: Literal[CardType.OFFENDER_PROFILE] = CardType.OFFENDER_PROFILE
    entity_id: str
    risk_level: Literal["critical", "high", "medium", "low"]
    risk_indicators: tuple[str, ...] = ()
    predicted_behavior: str
    confidence_score: float


class CriminalNetworkCard(CardModel):
    card_type: Literal[CardType.CRIMINAL_NETWORK] = CardType.CRIMINAL_NETWORK
    network_id: str
    members: tuple[dict[str, object], ...]
    total_edges: int
    density: float
    confidence_score: float


class FinancialTrailCard(CardModel):
    card_type: Literal[CardType.FINANCIAL_TRAIL] = CardType.FINANCIAL_TRAIL
    trail_id: str
    source_account: str
    destination_account: str
    hops: tuple[dict[str, object], ...]
    total_amount: float
    confidence_score: float


class CrimeHotspotCard(CardModel):
    card_type: Literal[CardType.CRIME_HOTSPOT] = CardType.CRIME_HOTSPOT
    hexagon_id: str
    district: str
    crime_category: str
    trend_direction: Literal["increasing", "stable", "decreasing"]
    forecast_confidence: float
    confidence_score: float


class SimilarCaseCard(CardModel):
    card_type: Literal[CardType.SIMILAR_CASE] = CardType.SIMILAR_CASE
    source_fir_id: str
    matched_fir_id: str
    overall_similarity: float
    similarity_dimensions: dict[str, object]
    confidence_score: float


class InvestigationTimelineCard(CardModel):
    card_type: Literal[CardType.INVESTIGATION_TIMELINE] = CardType.INVESTIGATION_TIMELINE
    investigation_id: str
    events: tuple[dict[str, object], ...]
    total_events: int
    completeness_score: float


class HypothesisCard(CardModel):
    card_type: Literal[CardType.HYPOTHESIS] = CardType.HYPOTHESIS
    hypothesis_id: str
    investigation_id: str
    statement: str
    status: Literal["active", "supported", "refuted", "inconclusive", "superseded"]
    confidence_score: float


class EvidenceSummaryCard(CardModel):
    card_type: Literal[CardType.EVIDENCE_SUMMARY] = CardType.EVIDENCE_SUMMARY
    investigation_id: str
    total_evidence_items: int
    categories: dict[str, object]
    overall_evidence_strength: float
    chain_of_custody_status: Literal["complete", "partial", "broken"]


class LeadCard(CardModel):
    card_type: Literal[CardType.LEAD] = CardType.LEAD
    lead_id: str
    investigation_id: str
    action: str
    rationale: str
    priority: Literal["critical", "high", "medium", "low"]
    confidence: float
    status: Literal["pending", "acted", "dismissed", "converted"]


class EntityResolutionCard(CardModel):
    card_type: Literal[CardType.ENTITY_RESOLUTION] = CardType.ENTITY_RESOLUTION
    resolution_id: str
    entity_a_id: str
    entity_b_id: str
    overall_confidence: float
    recommended_action: Literal["auto_merge", "officer_review", "no_action"]
    officer_action_required: bool = True


class ProactiveAlertCard(CardModel):
    card_type: Literal[CardType.PROACTIVE_ALERT] = CardType.PROACTIVE_ALERT
    alert_id: str
    investigation_id: str
    what_changed: str
    why_it_matters: str
    confidence: float
    urgency: Literal["immediate", "high", "routine"]
    status: Literal["new", "acknowledged", "acted", "dismissed", "expired"]


class SociologicalInsightCard(CardModel):
    card_type: Literal[CardType.SOCIOLOGICAL_INSIGHT] = CardType.SOCIOLOGICAL_INSIGHT
    insight_id: str
    area: dict[str, object]
    crime_type: str
    correlation_factors: tuple[dict[str, object], ...]
    qualification: str
    confidence_score: float


class ForecastCard(CardModel):
    card_type: Literal[CardType.FORECAST] = CardType.FORECAST
    forecast_id: str
    district: str
    crime_category: str
    forecasts: tuple[dict[str, object], ...]
    confidence_score: float


class CaseSummaryCard(CardModel):
    card_type: Literal[CardType.CASE_SUMMARY] = CardType.CASE_SUMMARY
    investigation_id: str
    summary_version: int
    key_facts: tuple[dict[str, object], ...]
    narrative: str
    investigation_progress: float


class ReasoningTraceCard(CardModel):
    card_type: Literal[CardType.REASONING_TRACE] = CardType.REASONING_TRACE
    trace_id: str
    parent_card_id: str
    parent_card_type: str
    question: str
    chain: tuple[dict[str, object], ...]
    conclusion: str
    conclusion_confidence: float


CardPayload = Annotated[
    Union[
        OffenderProfileCard, CriminalNetworkCard, FinancialTrailCard, CrimeHotspotCard, SimilarCaseCard,
        InvestigationTimelineCard, HypothesisCard, EvidenceSummaryCard, LeadCard, EntityResolutionCard,
        ProactiveAlertCard, SociologicalInsightCard, ForecastCard, CaseSummaryCard, ReasoningTraceCard,
    ],
    Field(discriminator="card_type"),
]


class CardProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    engine: str
    algorithm_version: str
    source_ids: tuple[str, ...]
    data_snapshot: str

    @field_validator("source_ids")
    @classmethod
    def source_ids_required(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("card provenance requires at least one source")
        return tuple(sorted(set(value)))


class CardRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    card_id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = 1
    status: CardStatus = CardStatus.ACTIVE
    generated_at: datetime
    stale_after: datetime
    payload: CardPayload
    provenance: CardProvenance
    supersedes_card_id: str | None = None
    superseded_by_card_id: str | None = None

    @field_validator("generated_at", "stale_after")
    @classmethod
    def aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("card timestamps must be timezone-aware")
        return value

    @field_validator("version")
    @classmethod
    def positive_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("card version must be positive")
        return value

    def as_of(self, at: datetime | None = None) -> "CardRecord":
        checked_at = at or datetime.now(timezone.utc)
        if self.status == CardStatus.ACTIVE and checked_at >= self.stale_after:
            return self.model_copy(update={"status": CardStatus.STALE})
        return self

    def mark_stale(self) -> "CardRecord":
        if self.status in {CardStatus.ARCHIVED, CardStatus.SUPERSEDED}:
            return self
        return self.model_copy(update={"status": CardStatus.STALE})

    def archive(self) -> "CardRecord":
        return self.model_copy(update={"status": CardStatus.ARCHIVED})

    def supersede(self, replacement_card_id: str) -> "CardRecord":
        if self.status == CardStatus.ARCHIVED:
            raise ValueError("archived cards cannot be superseded")
        return self.model_copy(update={"status": CardStatus.SUPERSEDED, "superseded_by_card_id": replacement_card_id})


ALL_CARD_TYPES = tuple(CardType)

__all__ = ["ALL_CARD_TYPES", "CardPayload", "CardProvenance", "CardRecord", "CardStatus", "CardType"] + [name for name in globals() if name.endswith("Card") and name != "CardRecord"]
