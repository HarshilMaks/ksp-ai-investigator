"""Pure lead mutations for the persistent investigation workspace."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain.enums import Priority
from src.domain.investigation_state import InvestigationState, Lead, LeadStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LeadService:
    def create(
        self,
        state: InvestigationState,
        *,
        actor_id: UUID,
        title: str,
        description: str,
        source_ids: tuple[str, ...],
        priority: Priority = Priority.MEDIUM,
        assigned_to: UUID | None = None,
    ) -> InvestigationState:
        lead = Lead(
            title=title,
            description=description,
            created_by=actor_id,
            source_ids=source_ids,
            lead_id=uuid4(),
            priority=priority,
            assigned_to=assigned_to,
        )
        return replace(state, leads=state.leads + (lead,), updated_at=_now())

    def update(
        self,
        state: InvestigationState,
        *,
        lead_id: UUID,
        status: LeadStatus | None = None,
        assigned_to: UUID | None = None,
        priority: Priority | None = None,
    ) -> InvestigationState:
        for index, current in enumerate(state.leads):
            if current.lead_id == lead_id:
                updated = replace(
                    current,
                    status=current.status if status is None else status,
                    assigned_to=current.assigned_to if assigned_to is None else assigned_to,
                    priority=current.priority if priority is None else priority,
                    updated_at=_now(),
                )
                values = list(state.leads)
                values[index] = updated
                return replace(state, leads=tuple(values), updated_at=_now())
        raise KeyError(f"unknown lead: {lead_id}")


__all__ = ["LeadService"]
