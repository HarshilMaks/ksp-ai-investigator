"""Persistent investigation workspace state contracts for P09.

The aggregate is application state, not an orchestration graph or agent memory
platform. It is serializable, versioned, and owned by the investigation service.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4

from src.shared.errors import ApplicationError

from .enums import Priority, TimelineEventType
from .models import InvestigationEvidence, TimelineEvent, to_record


class InvestigationStateError(ApplicationError, ValueError):
    """A P09 investigation state violates its lifecycle or field contract."""


class InvestigationLifecycle(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class HypothesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    SUPERSEDED = "SUPERSEDED"


class LeadStatus(str, Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DISMISSED = "DISMISSED"
    DEFERRED = "DEFERRED"


_ALLOWED_TRANSITIONS: dict[InvestigationLifecycle, frozenset[InvestigationLifecycle]] = {
    InvestigationLifecycle.CREATED: frozenset({InvestigationLifecycle.ACTIVE}),
    InvestigationLifecycle.ACTIVE: frozenset({InvestigationLifecycle.SUSPENDED, InvestigationLifecycle.CLOSED}),
    InvestigationLifecycle.SUSPENDED: frozenset({InvestigationLifecycle.ACTIVE, InvestigationLifecycle.CLOSED}),
    InvestigationLifecycle.CLOSED: frozenset({InvestigationLifecycle.ARCHIVED}),
    InvestigationLifecycle.ARCHIVED: frozenset(),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvestigationStateError("INVESTIGATION_REQUIRED_TEXT", f"{field_name} must be non-empty.")
    return value.strip()


def _aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvestigationStateError("INVESTIGATION_NAIVE_DATETIME", f"{field_name} must be timezone-aware.")
    return value


def _bounded(value: float, field_name: str) -> float:
    numeric = float(value)
    if not 0.0 <= numeric <= 1.0:
        raise InvestigationStateError("INVESTIGATION_OUT_OF_RANGE", f"{field_name} must be between 0 and 1.")
    return numeric


def _enum(value: Any, enum_type: type[Enum], field_name: str) -> Any:
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except ValueError as exc:
        raise InvestigationStateError("INVESTIGATION_INVALID_ENUM", f"{field_name} is invalid.") from exc


def _uuid(value: Any, field_name: str) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise InvestigationStateError("INVESTIGATION_INVALID_UUID", f"{field_name} must be a UUID.") from exc


@dataclass(frozen=True)
class InvestigationNote:
    text: str
    author_id: UUID
    note_id: UUID = field(default_factory=uuid4)
    tags: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", _text(self.text, "text"))
        object.__setattr__(self, "author_id", _uuid(self.author_id, "author_id"))
        object.__setattr__(self, "note_id", _uuid(self.note_id, "note_id"))
        object.__setattr__(self, "tags", tuple(_text(tag, "tag") for tag in self.tags))
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))


@dataclass(frozen=True)
class Hypothesis:
    statement: str
    created_by: UUID
    hypothesis_id: UUID = field(default_factory=uuid4)
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    supporting_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    contradicting_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    missing_critical_evidence: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "statement", _text(self.statement, "statement"))
        object.__setattr__(self, "created_by", _uuid(self.created_by, "created_by"))
        object.__setattr__(self, "hypothesis_id", _uuid(self.hypothesis_id, "hypothesis_id"))
        object.__setattr__(self, "status", _enum(self.status, HypothesisStatus, "status"))
        object.__setattr__(self, "supporting_evidence_ids", tuple(_text(value, "supporting_evidence_id") for value in self.supporting_evidence_ids))
        object.__setattr__(self, "contradicting_evidence_ids", tuple(_text(value, "contradicting_evidence_id") for value in self.contradicting_evidence_ids))
        object.__setattr__(self, "missing_critical_evidence", tuple(_text(value, "missing_critical_evidence") for value in self.missing_critical_evidence))
        object.__setattr__(self, "confidence", _bounded(self.confidence, "confidence"))
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))
        object.__setattr__(self, "updated_at", _aware(self.updated_at, "updated_at"))


@dataclass(frozen=True)
class Lead:
    title: str
    description: str
    created_by: UUID
    source_ids: tuple[str, ...]
    lead_id: UUID = field(default_factory=uuid4)
    status: LeadStatus = LeadStatus.OPEN
    priority: Priority = Priority.MEDIUM
    assigned_to: UUID | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "description", _text(self.description, "description"))
        object.__setattr__(self, "created_by", _uuid(self.created_by, "created_by"))
        object.__setattr__(self, "source_ids", tuple(_text(value, "source_id") for value in self.source_ids))
        if not self.source_ids:
            raise InvestigationStateError("INVESTIGATION_LEAD_SOURCE_REQUIRED", "A lead must have source evidence.")
        object.__setattr__(self, "lead_id", _uuid(self.lead_id, "lead_id"))
        object.__setattr__(self, "status", _enum(self.status, LeadStatus, "status"))
        object.__setattr__(self, "priority", _enum(self.priority, Priority, "priority"))
        if self.assigned_to is not None:
            object.__setattr__(self, "assigned_to", _uuid(self.assigned_to, "assigned_to"))
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))
        object.__setattr__(self, "updated_at", _aware(self.updated_at, "updated_at"))


@dataclass(frozen=True)
class GraphViewState:
    expanded_entity_ids: tuple[UUID, ...] = field(default_factory=tuple)
    selected_entity_id: UUID | None = None
    relationship_filters: tuple[str, ...] = field(default_factory=tuple)
    zoom: float = 1.0
    center_x: float = 0.0
    center_y: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "expanded_entity_ids", tuple(_uuid(value, "expanded_entity_id") for value in self.expanded_entity_ids))
        if self.selected_entity_id is not None:
            object.__setattr__(self, "selected_entity_id", _uuid(self.selected_entity_id, "selected_entity_id"))
        object.__setattr__(self, "relationship_filters", tuple(_text(value, "relationship_filter") for value in self.relationship_filters))
        if self.zoom <= 0:
            raise InvestigationStateError("INVESTIGATION_GRAPH_ZOOM_INVALID", "Graph zoom must be positive.")


@dataclass(frozen=True)
class HealthProvenance:
    metric: str
    source_ids: tuple[str, ...]
    calculation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "metric", _text(self.metric, "metric"))
        object.__setattr__(self, "source_ids", tuple(_text(value, "source_id") for value in self.source_ids))
        object.__setattr__(self, "calculation", _text(self.calculation, "calculation"))


@dataclass(frozen=True)
class InvestigationHealth:
    evidence_coverage: float
    timeline_completeness: float
    network_coverage: float
    financial_coverage: float
    witness_coverage: float
    contradiction_count: int
    missing_critical_evidence: tuple[str, ...]
    provenance: tuple[HealthProvenance, ...]
    calculated_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        for name in ("evidence_coverage", "timeline_completeness", "network_coverage", "financial_coverage", "witness_coverage"):
            object.__setattr__(self, name, _bounded(getattr(self, name), name))
        if self.contradiction_count < 0:
            raise InvestigationStateError("INVESTIGATION_NEGATIVE_CONTRADICTIONS", "Contradiction count cannot be negative.")
        object.__setattr__(self, "missing_critical_evidence", tuple(_text(value, "missing_critical_evidence") for value in self.missing_critical_evidence))
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "calculated_at", _aware(self.calculated_at, "calculated_at"))

    def as_percentages(self) -> dict[str, float]:
        return {
            "evidence_coverage": round(self.evidence_coverage * 100, 2),
            "timeline_completeness": round(self.timeline_completeness * 100, 2),
            "network_coverage": round(self.network_coverage * 100, 2),
            "financial_coverage": round(self.financial_coverage * 100, 2),
            "witness_coverage": round(self.witness_coverage * 100, 2),
        }


@dataclass(frozen=True)
class AuditMetadata:
    action: str
    officer_id: str
    request_id: str
    resource_id: UUID
    state_version: int
    timestamp: datetime
    previous_hash: str | None
    record_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", _text(self.action, "action"))
        object.__setattr__(self, "officer_id", _text(self.officer_id, "officer_id"))
        object.__setattr__(self, "request_id", _text(self.request_id, "request_id"))
        object.__setattr__(self, "resource_id", _uuid(self.resource_id, "resource_id"))
        if self.state_version < 1:
            raise InvestigationStateError("INVESTIGATION_AUDIT_VERSION_INVALID", "Audit state version must be positive.")
        object.__setattr__(self, "timestamp", _aware(self.timestamp, "timestamp"))
        object.__setattr__(self, "record_hash", _text(self.record_hash, "record_hash"))


@dataclass(frozen=True)
class InvestigationState:
    investigation_id: UUID
    title: str
    owner_id: UUID
    status: InvestigationLifecycle = InvestigationLifecycle.CREATED
    version: int = 1
    description: str | None = None
    primary_fir_id: UUID | None = None
    team_ids: tuple[UUID, ...] = field(default_factory=tuple)
    priority: Priority = Priority.MEDIUM
    evidence: tuple[InvestigationEvidence, ...] = field(default_factory=tuple)
    notes: tuple[InvestigationNote, ...] = field(default_factory=tuple)
    hypotheses: tuple[Hypothesis, ...] = field(default_factory=tuple)
    timeline: tuple[TimelineEvent, ...] = field(default_factory=tuple)
    leads: tuple[Lead, ...] = field(default_factory=tuple)
    graph_view: GraphViewState = field(default_factory=GraphViewState)
    health: InvestigationHealth | None = None
    audit_log: tuple[AuditMetadata, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    closed_at: datetime | None = None
    checkpoint_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "investigation_id", _uuid(self.investigation_id, "investigation_id"))
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "owner_id", _uuid(self.owner_id, "owner_id"))
        object.__setattr__(self, "status", _enum(self.status, InvestigationLifecycle, "status"))
        if self.version < 1:
            raise InvestigationStateError("INVESTIGATION_VERSION_INVALID", "Investigation state version must be positive.")
        if self.description is not None:
            object.__setattr__(self, "description", _text(self.description, "description"))
        if self.primary_fir_id is not None:
            object.__setattr__(self, "primary_fir_id", _uuid(self.primary_fir_id, "primary_fir_id"))
        object.__setattr__(self, "team_ids", tuple(_uuid(value, "team_id") for value in self.team_ids))
        object.__setattr__(self, "priority", _enum(self.priority, Priority, "priority"))
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))
        object.__setattr__(self, "updated_at", _aware(self.updated_at, "updated_at"))
        if self.closed_at is not None:
            object.__setattr__(self, "closed_at", _aware(self.closed_at, "closed_at"))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "notes", tuple(self.notes))
        object.__setattr__(self, "hypotheses", tuple(self.hypotheses))
        object.__setattr__(self, "timeline", tuple(self.timeline))
        object.__setattr__(self, "leads", tuple(self.leads))
        object.__setattr__(self, "audit_log", tuple(self.audit_log))

    def transition(self, target: InvestigationLifecycle) -> "InvestigationState":
        target = _enum(target, InvestigationLifecycle, "target")
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise InvestigationStateError(
                "INVESTIGATION_INVALID_TRANSITION",
                f"Cannot transition investigation from {self.status.value} to {target.value}.",
                details={"from": self.status.value, "to": target.value},
            )
        now = _now()
        return replace(
            self,
            status=target,
            closed_at=now if target == InvestigationLifecycle.CLOSED else self.closed_at,
            updated_at=now,
        )

    def with_version(self, version: int, *, checkpoint_id: str | None = None) -> "InvestigationState":
        return replace(self, version=version, checkpoint_id=checkpoint_id, updated_at=_now())

    def to_record(self) -> dict[str, Any]:
        return to_record(self)

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "InvestigationState":
        def dt(value: str) -> datetime:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

        def uid(value: str | None) -> UUID | None:
            return None if value is None else UUID(str(value))

        def evidence(value: Mapping[str, Any]) -> InvestigationEvidence:
            return InvestigationEvidence(
                investigation_id=UUID(str(value["investigation_id"])),
                pinned_by=UUID(str(value["pinned_by"])),
                entity_id=uid(value.get("entity_id")),
                fir_id=uid(value.get("fir_id")),
                note=value.get("note"),
                pinned_at=dt(value["pinned_at"]),
                tags=tuple(value.get("tags", [])),
                relevance_score=float(value.get("relevance_score", 1.0)),
            )

        notes = tuple(
            InvestigationNote(
                text=value["text"], author_id=UUID(str(value["author_id"])), note_id=UUID(str(value["note_id"])),
                tags=tuple(value.get("tags", [])), created_at=dt(value["created_at"]),
            )
            for value in record.get("notes", [])
        )
        hypotheses = tuple(
            Hypothesis(
                statement=value["statement"], created_by=UUID(str(value["created_by"])), hypothesis_id=UUID(str(value["hypothesis_id"])),
                status=value.get("status", HypothesisStatus.ACTIVE.value),
                supporting_evidence_ids=tuple(value.get("supporting_evidence_ids", [])),
                contradicting_evidence_ids=tuple(value.get("contradicting_evidence_ids", [])),
                missing_critical_evidence=tuple(value.get("missing_critical_evidence", [])),
                confidence=float(value.get("confidence", 0.0)), created_at=dt(value["created_at"]), updated_at=dt(value["updated_at"]),
            )
            for value in record.get("hypotheses", [])
        )
        leads = tuple(
            Lead(
                title=value["title"], description=value["description"], created_by=UUID(str(value["created_by"])),
                source_ids=tuple(value.get("source_ids", [])), lead_id=UUID(str(value["lead_id"])),
                status=value.get("status", LeadStatus.OPEN.value), priority=value.get("priority", Priority.MEDIUM.value),
                assigned_to=uid(value.get("assigned_to")), created_at=dt(value["created_at"]), updated_at=dt(value["updated_at"]),
            )
            for value in record.get("leads", [])
        )
        graph = record.get("graph_view", {})
        graph_view = GraphViewState(
            expanded_entity_ids=tuple(UUID(str(value)) for value in graph.get("expanded_entity_ids", [])),
            selected_entity_id=uid(graph.get("selected_entity_id")),
            relationship_filters=tuple(graph.get("relationship_filters", [])), zoom=float(graph.get("zoom", 1.0)),
            center_x=float(graph.get("center_x", 0.0)), center_y=float(graph.get("center_y", 0.0)),
        )
        health_record = record.get("health")
        health = None
        if health_record:
            health = InvestigationHealth(
                evidence_coverage=float(health_record["evidence_coverage"]), timeline_completeness=float(health_record["timeline_completeness"]),
                network_coverage=float(health_record["network_coverage"]), financial_coverage=float(health_record["financial_coverage"]),
                witness_coverage=float(health_record["witness_coverage"]), contradiction_count=int(health_record["contradiction_count"]),
                missing_critical_evidence=tuple(health_record.get("missing_critical_evidence", [])),
                provenance=tuple(HealthProvenance(**value) for value in health_record.get("provenance", [])),
                calculated_at=dt(health_record["calculated_at"]),
            )
        audit = tuple(
            AuditMetadata(
                action=value["action"], officer_id=value["officer_id"], request_id=value["request_id"],
                resource_id=UUID(str(value["resource_id"])), state_version=int(value["state_version"]), timestamp=dt(value["timestamp"]),
                previous_hash=value.get("previous_hash"), record_hash=value["record_hash"],
            )
            for value in record.get("audit_log", [])
        )
        timeline = tuple(
            TimelineEvent(
                investigation_id=UUID(str(value["investigation_id"])), event_time=dt(value["event_time"]),
                event_type=value["event_type"], description=value["description"], created_by=UUID(str(value["created_by"])),
                timeline_id=UUID(str(value["timeline_id"])), source_fir_id=uid(value.get("source_fir_id")),
                source_entity_id=uid(value.get("source_entity_id")), confidence=float(value.get("confidence", 1.0)),
                created_at=dt(value["created_at"]),
            )
            for value in record.get("timeline", [])
        )
        return cls(
            investigation_id=UUID(str(record["investigation_id"])), title=record["title"], owner_id=UUID(str(record["owner_id"])),
            status=record.get("status", InvestigationLifecycle.CREATED.value), version=int(record.get("version", 1)),
            description=record.get("description"), primary_fir_id=uid(record.get("primary_fir_id")),
            team_ids=tuple(UUID(str(value)) for value in record.get("team_ids", [])), priority=record.get("priority", Priority.MEDIUM.value),
            evidence=tuple(evidence(value) for value in record.get("evidence", [])), notes=notes, hypotheses=hypotheses,
            timeline=timeline, leads=leads, graph_view=graph_view, health=health, audit_log=audit,
            created_at=dt(record["created_at"]), updated_at=dt(record["updated_at"]),
            closed_at=dt(record["closed_at"]) if record.get("closed_at") else None,
            checkpoint_id=record.get("checkpoint_id"),
        )

    def latest_audit_hash(self) -> str | None:
        return self.audit_log[-1].record_hash if self.audit_log else None


__all__ = [
    "AuditMetadata", "GraphViewState", "HealthProvenance", "Hypothesis", "HypothesisStatus", "InvestigationHealth",
    "InvestigationLifecycle", "InvestigationNote", "InvestigationState", "InvestigationStateError", "Lead", "LeadStatus",
]
