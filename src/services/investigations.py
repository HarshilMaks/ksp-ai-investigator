"""P09 investigation lifecycle and synchronized workspace service."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import NAMESPACE_URL, UUID, uuid5

from src.domain.investigation_state import (
    AuditMetadata,
    GraphViewState,
    HypothesisStatus,
    InvestigationLifecycle,
    InvestigationState,
    InvestigationStateError,
    LeadStatus,
)
from src.domain.models import TimelineEvent
from src.domain.enums import Priority, TimelineEventType
from src.registry.tools import AuthorizationContext
from src.shared.errors import ApplicationError, new_request_id

from .checkpoints import CheckpointStore
from .evidence_board import EvidenceBoardService
from .hypotheses import HypothesisService
from .investigation_health import InvestigationHealthService
from .leads import LeadService


class InvestigationServiceError(ApplicationError):
    """Safe P09 service error."""


class InvestigationNotFound(InvestigationServiceError):
    """The requested investigation does not exist."""


class InvestigationAuthorizationError(InvestigationServiceError):
    """The officer is not authorized for the investigation operation."""


class InvestigationService:
    """Own lifecycle, persistence, authorization, synchronization, and audit metadata."""

    _elevated_roles = frozenset({"SHO", "DCP", "SP", "ADMIN"})

    def __init__(
        self,
        checkpoints: CheckpointStore,
        *,
        health: InvestigationHealthService | None = None,
        evidence_board: EvidenceBoardService | None = None,
        hypotheses: HypothesisService | None = None,
        leads: LeadService | None = None,
    ) -> None:
        self.checkpoints = checkpoints
        self.health = health or InvestigationHealthService()
        self.evidence_board = evidence_board or EvidenceBoardService()
        self.hypotheses = hypotheses or HypothesisService()
        self.leads = leads or LeadService()

    async def create(
        self,
        *,
        title: str,
        owner_id: UUID,
        authorization: AuthorizationContext,
        description: str | None = None,
        primary_fir_id: UUID | None = None,
        team_ids: tuple[UUID, ...] = (),
        priority: Priority = Priority.MEDIUM,
        request_id: str | None = None,
    ) -> InvestigationState:
        self._require_scope(authorization, write=True)
        actor_id = self._actor_uuid(authorization.officer_id)
        if actor_id != owner_id and authorization.role.upper() not in self._elevated_roles:
            raise InvestigationAuthorizationError(
                "INVESTIGATION_OWNER_MISMATCH",
                "The creating officer must be the investigation owner or an elevated supervisor.",
            )
        state = InvestigationState(
            investigation_id=uuid5(NAMESPACE_URL, f"ksp-investigation:{authorization.officer_id}:{title}:{datetime.now(timezone.utc).isoformat()}"),
            title=title,
            owner_id=owner_id,
            status=InvestigationLifecycle.CREATED,
            version=1,
            description=description,
            primary_fir_id=primary_fir_id,
            team_ids=team_ids,
            priority=priority,
        )
        state = replace(state, health=self.health.calculate(state))
        state = self._with_audit(state, authorization, "CREATE_INVESTIGATION", request_id or new_request_id(), 1)
        return await self.checkpoints.save(state, expected_version=None)

    async def get(self, investigation_id: UUID, *, authorization: AuthorizationContext) -> InvestigationState:
        state = await self.checkpoints.load(investigation_id)
        if state is None:
            raise InvestigationNotFound("INVESTIGATION_NOT_FOUND", "Investigation does not exist.", details={"investigation_id": str(investigation_id)})
        self._authorize(state, authorization, write=False)
        return state

    async def transition(
        self,
        investigation_id: UUID,
        target: InvestigationLifecycle,
        *,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        try:
            candidate = state.transition(target)
        except InvestigationStateError as exc:
            raise InvestigationServiceError(exc.code, str(exc), details=exc.details) from exc
        return await self._commit(state, candidate, authorization, "UPDATE_INVESTIGATION_STATUS", request_id)

    async def pin_evidence(
        self,
        investigation_id: UUID,
        *,
        fir_id: UUID | None = None,
        entity_id: UUID | None = None,
        note: str | None = None,
        tags: tuple[str, ...] = (),
        relevance_score: float = 1.0,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        if fir_id is None and entity_id is None:
            raise InvestigationServiceError("INVESTIGATION_EVIDENCE_TARGET_REQUIRED", "Evidence must target a FIR or entity.")
        candidate = self.evidence_board.pin(
            state, actor_id=self._actor_uuid(authorization.officer_id), fir_id=fir_id, entity_id=entity_id,
            note=note, tags=tags, relevance_score=relevance_score,
        )
        return await self._commit(state, candidate, authorization, "ADD_EVIDENCE", request_id)

    async def add_note(
        self,
        investigation_id: UUID,
        *,
        text: str,
        tags: tuple[str, ...] = (),
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        candidate = self.evidence_board.add_note(state, actor_id=self._actor_uuid(authorization.officer_id), text=text, tags=tags)
        return await self._commit(state, candidate, authorization, "ADD_NOTE", request_id)

    async def add_hypothesis(
        self,
        investigation_id: UUID,
        *,
        statement: str,
        supporting_evidence_ids: tuple[str, ...] = (),
        contradicting_evidence_ids: tuple[str, ...] = (),
        missing_critical_evidence: tuple[str, ...] = (),
        confidence: float = 0.0,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        candidate = self.hypotheses.create(
            state, actor_id=self._actor_uuid(authorization.officer_id), statement=statement,
            supporting_evidence_ids=supporting_evidence_ids, contradicting_evidence_ids=contradicting_evidence_ids,
            missing_critical_evidence=missing_critical_evidence, confidence=confidence,
        )
        return await self._commit(state, candidate, authorization, "UPDATE_HYPOTHESIS", request_id)

    async def update_hypothesis(
        self,
        investigation_id: UUID,
        hypothesis_id: UUID,
        *,
        status: HypothesisStatus | None = None,
        supporting_evidence_ids: tuple[str, ...] | None = None,
        contradicting_evidence_ids: tuple[str, ...] | None = None,
        missing_critical_evidence: tuple[str, ...] | None = None,
        confidence: float | None = None,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        try:
            candidate = self.hypotheses.update(
                state, hypothesis_id=hypothesis_id, status=status, supporting_evidence_ids=supporting_evidence_ids,
                contradicting_evidence_ids=contradicting_evidence_ids, missing_critical_evidence=missing_critical_evidence,
                confidence=confidence,
            )
        except KeyError as exc:
            raise InvestigationServiceError("INVESTIGATION_HYPOTHESIS_NOT_FOUND", str(exc)) from exc
        return await self._commit(state, candidate, authorization, "UPDATE_HYPOTHESIS", request_id)

    async def add_timeline_event(
        self,
        investigation_id: UUID,
        *,
        event_time: datetime,
        event_type: TimelineEventType,
        description: str,
        source_fir_id: UUID | None = None,
        source_entity_id: UUID | None = None,
        confidence: float = 1.0,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        event = TimelineEvent(
            investigation_id=investigation_id, event_time=event_time, event_type=event_type, description=description,
            created_by=self._actor_uuid(authorization.officer_id), source_fir_id=source_fir_id,
            source_entity_id=source_entity_id, confidence=confidence,
        )
        candidate = replace(state, timeline=state.timeline + (event,), updated_at=datetime.now(timezone.utc))
        return await self._commit(state, candidate, authorization, "ADD_TIMELINE_EVENT", request_id)

    async def add_lead(
        self,
        investigation_id: UUID,
        *,
        title: str,
        description: str,
        source_ids: tuple[str, ...],
        priority: Priority = Priority.MEDIUM,
        assigned_to: UUID | None = None,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        candidate = self.leads.create(
            state, actor_id=self._actor_uuid(authorization.officer_id), title=title, description=description,
            source_ids=source_ids, priority=priority, assigned_to=assigned_to,
        )
        return await self._commit(state, candidate, authorization, "UPDATE_LEAD", request_id)

    async def update_lead(
        self,
        investigation_id: UUID,
        lead_id: UUID,
        *,
        status: LeadStatus | None = None,
        assigned_to: UUID | None = None,
        priority: Priority | None = None,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        try:
            candidate = self.leads.update(state, lead_id=lead_id, status=status, assigned_to=assigned_to, priority=priority)
        except KeyError as exc:
            raise InvestigationServiceError("INVESTIGATION_LEAD_NOT_FOUND", str(exc)) from exc
        return await self._commit(state, candidate, authorization, "UPDATE_LEAD", request_id)

    async def update_graph_view(
        self,
        investigation_id: UUID,
        *,
        expanded_entity_ids: tuple[UUID, ...] = (),
        selected_entity_id: UUID | None = None,
        relationship_filters: tuple[str, ...] = (),
        zoom: float = 1.0,
        center_x: float = 0.0,
        center_y: float = 0.0,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> InvestigationState:
        state = await self._load_for_write(investigation_id, authorization)
        candidate = replace(
            state,
            graph_view=GraphViewState(
                expanded_entity_ids=expanded_entity_ids, selected_entity_id=selected_entity_id,
                relationship_filters=relationship_filters, zoom=zoom, center_x=center_x, center_y=center_y,
            ),
            updated_at=datetime.now(timezone.utc),
        )
        return await self._commit(state, candidate, authorization, "UPDATE_GRAPH_VIEW", request_id)

    async def _load_for_write(self, investigation_id: UUID, authorization: AuthorizationContext) -> InvestigationState:
        state = await self.get(investigation_id, authorization=authorization)
        self._authorize(state, authorization, write=True)
        if state.status == InvestigationLifecycle.ARCHIVED:
            raise InvestigationServiceError("INVESTIGATION_ARCHIVED_READ_ONLY", "Archived investigations are read-only.")
        return state

    async def _commit(
        self,
        previous: InvestigationState,
        candidate: InvestigationState,
        authorization: AuthorizationContext,
        action: str,
        request_id: str | None,
    ) -> InvestigationState:
        versioned = candidate.with_version(previous.version + 1)
        versioned = replace(versioned, health=self.health.calculate(versioned))
        versioned = self._with_audit(versioned, authorization, action, request_id or new_request_id(), versioned.version, previous.latest_audit_hash())
        return await self.checkpoints.save(versioned, expected_version=previous.version)

    def _with_audit(
        self,
        state: InvestigationState,
        authorization: AuthorizationContext,
        action: str,
        request_id: str,
        version: int,
        previous_hash: str | None = None,
    ) -> InvestigationState:
        timestamp = datetime.now(timezone.utc)
        payload = {
            "action": action, "officer_id": authorization.officer_id, "request_id": request_id,
            "resource_id": str(state.investigation_id), "state_version": version,
            "timestamp": timestamp.isoformat(), "previous_hash": previous_hash,
        }
        record_hash = hashlib.sha512(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        entry = AuditMetadata(
            action=action, officer_id=authorization.officer_id, request_id=request_id,
            resource_id=state.investigation_id, state_version=version, timestamp=timestamp,
            previous_hash=previous_hash, record_hash=record_hash,
        )
        return replace(state, audit_log=state.audit_log + (entry,), updated_at=timestamp)

    def _authorize(self, state: InvestigationState, authorization: AuthorizationContext, *, write: bool) -> None:
        self._require_scope(authorization, write=write)
        if authorization.investigation_id is not None and authorization.investigation_id != str(state.investigation_id):
            raise InvestigationAuthorizationError("INVESTIGATION_SCOPE_FORBIDDEN", "Authorization is outside the investigation scope.")
        actor_id = self._actor_uuid(authorization.officer_id)
        member = actor_id == state.owner_id or actor_id in state.team_ids
        if not member and authorization.role.upper() not in self._elevated_roles:
            raise InvestigationAuthorizationError("INVESTIGATION_MEMBER_FORBIDDEN", "Officer is not assigned to this investigation.")

    @staticmethod
    def _require_scope(authorization: AuthorizationContext, *, write: bool) -> None:
        required = "investigation:write" if write else "investigation:read"
        if required not in authorization.scopes and not (not write and "investigation:write" in authorization.scopes) and "investigation:admin" not in authorization.scopes and authorization.role.upper() not in {"SHO", "DCP", "SP", "ADMIN"}:
            raise InvestigationAuthorizationError("INVESTIGATION_PERMISSION_REQUIRED", f"{required} permission is required.")

    @staticmethod
    def _actor_uuid(officer_id: str) -> UUID:
        try:
            return UUID(officer_id)
        except (ValueError, AttributeError):
            return uuid5(NAMESPACE_URL, f"ksp-officer:{officer_id}")


__all__ = ["InvestigationAuthorizationError", "InvestigationNotFound", "InvestigationService", "InvestigationServiceError"]
