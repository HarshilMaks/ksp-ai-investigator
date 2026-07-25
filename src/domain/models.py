"""Validated logical records mirroring database-schema.md tables.

These are local contracts only. Catalyst Data Store compatibility and persistence
are adapter concerns; this module does not emit PostgreSQL DDL or perform I/O.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4

from src.shared.errors import ApplicationError
from src.shared.ports import JsonObject

from .enums import (
    AuditAction,
    CardType,
    DiscoveryMethod,
    EntityType,
    ExtractionMethod,
    FIREntityRole,
    FIRStatus,
    InvestigationStatus,
    Priority,
    RelationshipType,
    TimelineEventType,
)


class ModelValidationError(ApplicationError, ValueError):
    """A logical data contract violates a locked constraint."""


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelValidationError("MODEL_REQUIRED_TEXT", f"{field_name} must be non-empty.")
    return value.strip()


def _bounded(value: float, field_name: str, minimum: float = 0.0, maximum: float = 1.0) -> float:
    numeric = float(value)
    if not minimum <= numeric <= maximum:
        raise ModelValidationError(
            "MODEL_OUT_OF_RANGE",
            f"{field_name} must be between {minimum} and {maximum}.",
            details={"field": field_name},
        )
    return numeric


def _aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ModelValidationError("MODEL_NAIVE_DATETIME", f"{field_name} must be timezone-aware.")
    return value


def _enum(value: Any, enum_type: type[Enum], field_name: str) -> Any:
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except ValueError as exc:
        raise ModelValidationError(
            "MODEL_INVALID_ENUM",
            f"{field_name} is not in the locked vocabulary.",
            details={"field": field_name, "value": str(value)},
        ) from exc


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FIR:
    fir_number: str
    ps_code: str
    district: str
    crime_date: datetime
    registration_date: datetime
    ipc_sections: tuple[int, ...]
    crime_category: str
    fir_id: UUID = field(default_factory=uuid4)
    crime_subtype: str | None = None
    narrative_en: str | None = None
    narrative_kn: str | None = None
    narrative_vec: tuple[float, ...] | None = None
    status: FIRStatus = FIRStatus.OPEN
    priority: Priority = Priority.MEDIUM
    modus_operandi: JsonObject = field(default_factory=dict)
    complainant_name: str | None = None
    io_officer_id: UUID | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        self.fir_number = _require_text(self.fir_number, "fir_number")
        self.ps_code = _require_text(self.ps_code, "ps_code")
        self.district = _require_text(self.district, "district")
        self.crime_category = _require_text(self.crime_category, "crime_category")
        self.crime_date = _aware(self.crime_date, "crime_date")
        self.registration_date = _aware(self.registration_date, "registration_date")
        self.created_at = _aware(self.created_at, "created_at")
        self.updated_at = _aware(self.updated_at, "updated_at")
        self.ipc_sections = tuple(int(section) for section in self.ipc_sections)
        self.status = _enum(self.status, FIRStatus, "status")
        self.priority = _enum(self.priority, Priority, "priority")
        if self.narrative_vec is not None and len(self.narrative_vec) != 1024:
            raise ModelValidationError(
                "MODEL_INVALID_VECTOR_DIMENSIONS",
                "narrative_vec must be 1024-dimensional when present.",
            )


@dataclass
class Entity:
    entity_type: EntityType
    entity_value: str
    canonical_value: str
    entity_id: UUID = field(default_factory=uuid4)
    attributes: JsonObject = field(default_factory=dict)
    first_seen: datetime = field(default_factory=_now)
    last_seen: datetime = field(default_factory=_now)
    risk_score: float = 0.0
    merged_into: UUID | None = None
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        self.entity_type = _enum(self.entity_type, EntityType, "entity_type")
        self.entity_value = _require_text(self.entity_value, "entity_value")
        self.canonical_value = _require_text(self.canonical_value, "canonical_value")
        self.risk_score = _bounded(self.risk_score, "risk_score")
        for name in ("first_seen", "last_seen", "created_at"):
            setattr(self, name, _aware(getattr(self, name), name))


@dataclass
class FIREntityLink:
    fir_id: UUID
    entity_id: UUID
    role: FIREntityRole
    confidence: float = 1.0
    extraction_method: ExtractionMethod = ExtractionMethod.MANUAL
    extracted_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        self.role = _enum(self.role, FIREntityRole, "role")
        self.extraction_method = _enum(self.extraction_method, ExtractionMethod, "extraction_method")
        self.confidence = _bounded(self.confidence, "confidence")
        self.extracted_at = _aware(self.extracted_at, "extracted_at")


@dataclass
class Relationship:
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: RelationshipType
    relationship_id: UUID = field(default_factory=uuid4)
    strength: float = 1.0
    evidence_fir_ids: tuple[UUID, ...] = field(default_factory=tuple)
    discovered_at: datetime = field(default_factory=_now)
    discovery_method: DiscoveryMethod = DiscoveryMethod.MANUAL
    verified: bool = False
    verified_by: UUID | None = None
    verified_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        self.relationship_type = _enum(self.relationship_type, RelationshipType, "relationship_type")
        self.discovery_method = _enum(self.discovery_method, DiscoveryMethod, "discovery_method")
        self.strength = _bounded(self.strength, "strength", 0.0, 1.5)
        self.evidence_fir_ids = tuple(self.evidence_fir_ids)
        self.discovered_at = _aware(self.discovered_at, "discovered_at")
        for name in ("verified_at", "expires_at"):
            value = getattr(self, name)
            if value is not None:
                setattr(self, name, _aware(value, name))
        if self.verified and not self.evidence_fir_ids:
            raise ModelValidationError(
                "MODEL_VERIFIED_RELATIONSHIP_NEEDS_EVIDENCE",
                "A verified relationship must reference at least one evidence FIR.",
            )
        if self.verified and (self.verified_by is None or self.verified_at is None):
            raise ModelValidationError(
                "MODEL_VERIFICATION_METADATA_REQUIRED",
                "Verified relationships require verifier and verification timestamp.",
            )


@dataclass
class Investigation:
    title: str
    owner_id: UUID
    investigation_id: UUID = field(default_factory=uuid4)
    description: str | None = None
    primary_fir_id: UUID | None = None
    status: InvestigationStatus = InvestigationStatus.OPEN
    team_ids: tuple[UUID, ...] = field(default_factory=tuple)
    hypothesis: str | None = None
    priority: Priority = Priority.MEDIUM
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        self.title = _require_text(self.title, "title")
        self.status = _enum(self.status, InvestigationStatus, "status")
        self.priority = _enum(self.priority, Priority, "priority")
        self.team_ids = tuple(self.team_ids)
        for name in ("created_at", "updated_at", "closed_at"):
            value = getattr(self, name)
            if value is not None:
                setattr(self, name, _aware(value, name))
        if self.status == InvestigationStatus.CLOSED and self.closed_at is None:
            raise ModelValidationError("MODEL_CLOSED_INVESTIGATION_NEEDS_DATE", "Closed investigations need closed_at.")


@dataclass
class InvestigationEvidence:
    investigation_id: UUID
    pinned_by: UUID
    entity_id: UUID | None = None
    fir_id: UUID | None = None
    note: str | None = None
    pinned_at: datetime = field(default_factory=_now)
    tags: tuple[str, ...] = field(default_factory=tuple)
    relevance_score: float = 1.0

    def __post_init__(self) -> None:
        if self.entity_id is None and self.fir_id is None:
            raise ModelValidationError("MODEL_EVIDENCE_TARGET_REQUIRED", "Evidence must target an entity or FIR.")
        self.pinned_at = _aware(self.pinned_at, "pinned_at")
        self.relevance_score = _bounded(self.relevance_score, "relevance_score")
        self.tags = tuple(_require_text(tag, "tag") for tag in self.tags)


@dataclass
class TimelineEvent:
    investigation_id: UUID
    event_time: datetime
    event_type: TimelineEventType
    description: str
    created_by: UUID
    timeline_id: UUID = field(default_factory=uuid4)
    source_fir_id: UUID | None = None
    source_entity_id: UUID | None = None
    confidence: float = 1.0
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        self.event_type = _enum(self.event_type, TimelineEventType, "event_type")
        self.description = _require_text(self.description, "description")
        self.event_time = _aware(self.event_time, "event_time")
        self.created_at = _aware(self.created_at, "created_at")
        self.confidence = _bounded(self.confidence, "confidence")


@dataclass
class EngineRun:
    engine_name: str
    tool_id: str
    input_hash: str
    status: str
    run_id: UUID = field(default_factory=uuid4)
    output_ref: str | None = None
    source_snapshot: JsonObject = field(default_factory=dict)
    computed_at: datetime = field(default_factory=_now)
    expires_at: datetime | None = None
    audit_metadata: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("engine_name", "tool_id", "input_hash", "status"):
            setattr(self, name, _require_text(getattr(self, name), name))
        if len(self.tool_id) > 3:
            raise ModelValidationError("MODEL_INVALID_TOOL_ID", "tool_id must use the T01-T23 three-character form.")
        self.computed_at = _aware(self.computed_at, "computed_at")
        if self.expires_at is not None:
            self.expires_at = _aware(self.expires_at, "expires_at")


@dataclass
class EvidenceProvenance:
    claim_id: str
    source_type: str
    source_id: str
    provenance_id: UUID = field(default_factory=uuid4)
    run_id: UUID | None = None
    calculation: JsonObject = field(default_factory=dict)
    permission_scope: JsonObject = field(default_factory=dict)
    contradiction_refs: tuple[str, ...] = field(default_factory=tuple)
    confidence: float | None = None
    validated_at: datetime | None = None
    validator_version: str | None = None

    def __post_init__(self) -> None:
        for name in ("claim_id", "source_type", "source_id"):
            setattr(self, name, _require_text(getattr(self, name), name))
        self.contradiction_refs = tuple(self.contradiction_refs)
        if self.confidence is not None:
            self.confidence = _bounded(self.confidence, "confidence")
        if self.validated_at is not None:
            self.validated_at = _aware(self.validated_at, "validated_at")


@dataclass
class IntelligenceCard:
    card_type: CardType
    data: JsonObject
    valid_until: datetime
    card_id: UUID = field(default_factory=uuid4)
    subject_entity_id: UUID | None = None
    subject_fir_id: UUID | None = None
    generated_at: datetime = field(default_factory=_now)
    version: int = 1
    generated_by: str = "SYSTEM"
    superseded_by: UUID | None = None

    def __post_init__(self) -> None:
        self.card_type = _enum(self.card_type, CardType, "card_type")
        if self.subject_entity_id is None and self.subject_fir_id is None:
            raise ModelValidationError("MODEL_CARD_SUBJECT_REQUIRED", "An intelligence card needs an entity or FIR subject.")
        if self.version < 1:
            raise ModelValidationError("MODEL_CARD_VERSION_INVALID", "Card version must be positive.")
        self.generated_at = _aware(self.generated_at, "generated_at")
        self.valid_until = _aware(self.valid_until, "valid_until")
        self.generated_by = _require_text(self.generated_by, "generated_by")


@dataclass
class AuditLog:
    user_id: UUID
    user_role: str
    action: AuditAction
    resource_type: str
    resource_id: str
    hash_chain: str
    log_id: int | None = None
    timestamp: datetime = field(default_factory=_now)
    details: JsonObject = field(default_factory=dict)
    ip_address: str | None = None
    session_id: UUID | None = None
    prev_hash: str | None = None

    def __post_init__(self) -> None:
        self.user_role = _require_text(self.user_role, "user_role")
        self.action = _enum(self.action, AuditAction, "action")
        self.resource_type = _require_text(self.resource_type, "resource_type")
        self.resource_id = _require_text(self.resource_id, "resource_id")
        self.hash_chain = _require_text(self.hash_chain, "hash_chain")
        self.timestamp = _aware(self.timestamp, "timestamp")


def to_record(value: Any) -> Any:
    """Convert a domain object to JSON-compatible logical record data."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if is_dataclass(value):
        return {field.name: to_record(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_record(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_record(item) for item in value]
    return value
