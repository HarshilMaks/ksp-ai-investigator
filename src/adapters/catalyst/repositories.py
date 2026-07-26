"""Typed Catalyst Data Store repositories over the validated DataStorePort.

These repositories deliberately contain no Catalyst SDK calls. The injected
DataStorePort owns transport and deployment behavior; this module owns exact
logical table names, keys, row serialization, and normalized state mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping
from uuid import NAMESPACE_URL, UUID, uuid5

from src.domain.cards import CardRecord
from src.domain.investigation_state import InvestigationState
from src.domain.models import (
    EngineRun,
    Entity,
    EvidenceProvenance,
    FIR,
    FIREntityLink,
    IntelligenceCard,
    InvestigationEvidence,
    Relationship,
    TimelineEvent,
    to_record,
)
from src.shared.errors import ApplicationError
from src.shared.ports import DataStorePort, JsonObject


LOGICAL_CATALYST_TABLES = (
    "engine_runs",
    "evidence_provenance",
    "firs",
    "entities",
    "fir_entities",
    "relationships",
    "investigations",
    "investigation_evidence",
    "investigation_timeline",
    "intelligence_cards",
    "audit_logs",
)


class CatalystRepositoryError(ApplicationError):
    """A repository operation or logical row mapping failed."""


class CatalystTableRepository:
    """Generic async CRUD boundary for one logical Catalyst table."""

    table_name: ClassVar[str]
    key_field: ClassVar[str]

    def __init__(self, data_store: DataStorePort) -> None:
        self.data_store = data_store

    async def get(self, key: str) -> JsonObject | None:
        return await self.data_store.get(self.table_name, str(key))

    async def create(self, row: Mapping[str, Any], *, key: str | None = None) -> JsonObject:
        normalized = _row(row)
        record_key = key or self.key_for(normalized)
        if await self.get(record_key) is not None:
            raise CatalystRepositoryError(
                "CATALYST_RECORD_EXISTS",
                "A record with this logical key already exists.",
                details={"table": self.table_name, "key": record_key},
            )
        await self.data_store.put(self.table_name, record_key, normalized)
        return normalized

    async def update(self, key: str, row: Mapping[str, Any]) -> JsonObject:
        record_key = str(key)
        if await self.get(record_key) is None:
            raise CatalystRepositoryError(
                "CATALYST_RECORD_NOT_FOUND",
                "The requested Catalyst record does not exist.",
                details={"table": self.table_name, "key": record_key},
            )
        normalized = _row(row)
        await self.data_store.put(self.table_name, record_key, normalized)
        return normalized

    async def upsert(self, row: Mapping[str, Any], *, key: str | None = None) -> JsonObject:
        normalized = _row(row)
        record_key = key or self.key_for(normalized)
        await self.data_store.put(self.table_name, record_key, normalized)
        return normalized

    async def delete(self, key: str) -> None:
        await self.data_store.delete(self.table_name, str(key))

    async def list(self, filters: Mapping[str, Any] | None = None) -> tuple[JsonObject, ...]:
        values = await self.data_store.query(self.table_name, dict(filters or {}))
        return tuple(dict(value) for value in values)

    def key_for(self, row: Mapping[str, Any]) -> str:
        try:
            value = row[self.key_field]
        except KeyError as exc:
            raise CatalystRepositoryError(
                "CATALYST_KEY_REQUIRED",
                "A logical table row is missing its primary key.",
                details={"table": self.table_name, "key_field": self.key_field},
            ) from exc
        return str(value)


class EngineRunRepository(CatalystTableRepository):
    table_name = "engine_runs"
    key_field = "run_id"

    async def save(self, record: EngineRun) -> JsonObject:
        return await self.upsert(to_record(record))


class EvidenceProvenanceRepository(CatalystTableRepository):
    table_name = "evidence_provenance"
    key_field = "provenance_id"

    async def save(self, record: EvidenceProvenance) -> JsonObject:
        return await self.upsert(to_record(record))


class FIRRepository(CatalystTableRepository):
    table_name = "firs"
    key_field = "fir_id"

    async def save(self, record: FIR) -> JsonObject:
        return await self.upsert(to_record(record))


class EntityRepository(CatalystTableRepository):
    table_name = "entities"
    key_field = "entity_id"

    async def save(self, record: Entity) -> JsonObject:
        return await self.upsert(to_record(record))


class FIREntityLinkRepository(CatalystTableRepository):
    table_name = "fir_entities"
    key_field = "fir_id"

    def key_for(self, row: Mapping[str, Any]) -> str:
        try:
            return f"{row['fir_id']}:{row['entity_id']}:{row['role']}"
        except KeyError as exc:
            raise CatalystRepositoryError(
                "CATALYST_COMPOSITE_KEY_REQUIRED",
                "FIR/entity links require fir_id, entity_id, and role.",
                details={"table": self.table_name},
            ) from exc

    async def save(self, record: FIREntityLink) -> JsonObject:
        return await self.upsert(to_record(record))


class RelationshipRepository(CatalystTableRepository):
    table_name = "relationships"
    key_field = "relationship_id"

    async def save(self, record: Relationship) -> JsonObject:
        return await self.upsert(to_record(record))


class InvestigationRepository(CatalystTableRepository):
    table_name = "investigations"
    key_field = "investigation_id"

    async def save_state(self, state: InvestigationState) -> JsonObject:
        # The normalized table predates P09's CREATED/ARCHIVED workspace states.
        # The complete state remains in investigation_checkpoints; this row is
        # the compatible normalized index/metadata projection.
        status = {
            "CREATED": "OPEN",
            "ARCHIVED": "CLOSED",
        }.get(state.status.value, state.status.value)
        hypothesis = state.hypotheses[-1].statement if state.hypotheses else None
        row = {
            "investigation_id": str(state.investigation_id),
            "title": state.title,
            "description": state.description,
            "primary_fir_id": _optional_uuid(state.primary_fir_id),
            "status": status,
            "owner_id": str(state.owner_id),
            "team_ids": [str(value) for value in state.team_ids],
            "hypothesis": hypothesis,
            "priority": state.priority.value,
            "created_at": to_record(state.created_at),
            "updated_at": to_record(state.updated_at),
            "closed_at": to_record(state.closed_at) if state.closed_at else None,
        }
        return await self.upsert(row)


class InvestigationEvidenceRepository(CatalystTableRepository):
    table_name = "investigation_evidence"
    key_field = "investigation_id"

    def key_for(self, row: Mapping[str, Any]) -> str:
        return ":".join(
            (
                str(row["investigation_id"]),
                str(row.get("entity_id") or ""),
                str(row.get("fir_id") or ""),
            )
        )

    async def save(self, record: InvestigationEvidence) -> JsonObject:
        return await self.upsert(to_record(record))


class InvestigationTimelineRepository(CatalystTableRepository):
    table_name = "investigation_timeline"
    key_field = "timeline_id"

    async def save(self, record: TimelineEvent) -> JsonObject:
        return await self.upsert(to_record(record))


class IntelligenceCardRepository(CatalystTableRepository):
    table_name = "intelligence_cards"
    key_field = "card_id"

    async def save_legacy(self, record: IntelligenceCard) -> JsonObject:
        return await self.upsert(to_record(record))

    async def save_card(self, record: CardRecord) -> JsonObject:
        payload = record.payload.model_dump(mode="json")
        row = {
            "card_id": record.card_id,
            # Preserve the active P14 payload vocabulary. Catalyst schema
            # validation must reconcile its 15 types with the legacy five-type
            # logical CHECK constraint before deployment.
            "card_type": record.payload.card_type.value,
            "subject_entity_id": _first(payload, "entity_id", "entity_a_id", "entity_b_id"),
            "subject_fir_id": _first(payload, "investigation_id", "source_fir_id", "matched_fir_id"),
            "data": record.model_dump(mode="json"),
            "generated_at": to_record(record.generated_at),
            "valid_until": to_record(record.stale_after),
            "version": record.version,
            "generated_by": record.provenance.engine,
            "superseded_by": record.superseded_by_card_id,
        }
        return await self.upsert(row, key=f"{record.card_id}:v{record.version}")

    async def get_card(self, card_id: str, version: int | None = None) -> CardRecord | None:
        if version is not None:
            row = await self.get(f"{card_id}:v{version}")
            return _card_from_row(row)
        rows = await self.list({"card_id": card_id})
        if not rows:
            return None
        row = max(rows, key=lambda value: int(value.get("version", 0)))
        return _card_from_row(row)


class AuditLogRepository(CatalystTableRepository):
    table_name = "audit_logs"
    # audit_logs.log_id is BIGSERIAL in the logical schema. The repository uses
    # a deterministic external key and leaves physical sequence assignment to
    # the Catalyst table/transport implementation.
    key_field = "resource_id"

    async def save_state_audit(
        self,
        state: InvestigationState,
        *,
        user_role: str = "APPLICATION",
    ) -> tuple[JsonObject, ...]:
        saved: list[JsonObject] = []
        for entry in state.audit_log:
            user_id = _as_uuid(entry.officer_id)
            row = {
                "timestamp": to_record(entry.timestamp),
                "user_id": str(user_id),
                "user_role": user_role,
                "action": _audit_action(entry.action),
                "resource_type": "investigation",
                "resource_id": str(entry.resource_id),
                "details": {
                    "request_id": entry.request_id,
                    "state_version": entry.state_version,
                },
                "hash_chain": entry.record_hash,
                "prev_hash": entry.previous_hash,
            }
            key = f"{entry.resource_id}:v{entry.state_version}"
            saved.append(await self.upsert(row, key=key))
        return tuple(saved)


@dataclass(frozen=True)
class CatalystRepositorySet:
    """All logical Catalyst repositories used by the application boundary."""

    engine_runs: EngineRunRepository
    evidence_provenance: EvidenceProvenanceRepository
    firs: FIRRepository
    entities: EntityRepository
    fir_entities: FIREntityLinkRepository
    relationships: RelationshipRepository
    investigations: InvestigationRepository
    investigation_evidence: InvestigationEvidenceRepository
    investigation_timeline: InvestigationTimelineRepository
    intelligence_cards: IntelligenceCardRepository
    audit_logs: AuditLogRepository

    @classmethod
    def from_data_store(cls, data_store: DataStorePort) -> "CatalystRepositorySet":
        return cls(
            engine_runs=EngineRunRepository(data_store),
            evidence_provenance=EvidenceProvenanceRepository(data_store),
            firs=FIRRepository(data_store),
            entities=EntityRepository(data_store),
            fir_entities=FIREntityLinkRepository(data_store),
            relationships=RelationshipRepository(data_store),
            investigations=InvestigationRepository(data_store),
            investigation_evidence=InvestigationEvidenceRepository(data_store),
            investigation_timeline=InvestigationTimelineRepository(data_store),
            intelligence_cards=IntelligenceCardRepository(data_store),
            audit_logs=AuditLogRepository(data_store),
        )

    async def persist_investigation_state(
        self,
        state: InvestigationState,
        *,
        user_role: str = "APPLICATION",
    ) -> None:
        await self.investigations.save_state(state)
        for evidence in state.evidence:
            await self.investigation_evidence.save(evidence)
        for event in state.timeline:
            await self.investigation_timeline.save(event)
        await self.audit_logs.save_state_audit(state, user_role=user_role)


def _row(value: Mapping[str, Any]) -> JsonObject:
    return {str(key): _json_value(item) for key, item in value.items()}


def _json_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _optional_uuid(value: UUID | None) -> str | None:
    return None if value is None else str(value)


def _first(payload: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        value = payload.get(name)
        if value is not None:
            return str(value)
    return None


def _as_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        return uuid5(NAMESPACE_URL, f"ksp-audit-officer:{value}")


def _audit_action(action: str) -> str:
    if action == "CREATE_INVESTIGATION":
        return action
    if action == "ADD_EVIDENCE":
        return action
    if action in {"UPDATE_INVESTIGATION_STATUS", "ADD_NOTE", "UPDATE_HYPOTHESIS", "UPDATE_LEAD", "UPDATE_GRAPH_VIEW"}:
        return "UPDATE"
    return "UPDATE"


def _card_from_row(row: JsonObject | None) -> CardRecord | None:
    if row is None:
        return None
    data = row.get("data")
    if not isinstance(data, Mapping):
        return None
    try:
        return CardRecord.model_validate(data)
    except (TypeError, ValueError):
        return None


__all__ = [
    "AuditLogRepository",
    "CatalystRepositoryError",
    "CatalystRepositorySet",
    "CatalystTableRepository",
    "EngineRunRepository",
    "EntityRepository",
    "EvidenceProvenanceRepository",
    "FIREntityLinkRepository",
    "FIRRepository",
    "IntelligenceCardRepository",
    "InvestigationEvidenceRepository",
    "InvestigationRepository",
    "InvestigationTimelineRepository",
    "LOGICAL_CATALYST_TABLES",
    "RelationshipRepository",
]
