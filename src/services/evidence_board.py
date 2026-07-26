"""Pure evidence-board mutations used by InvestigationService."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain.investigation_state import InvestigationNote, InvestigationState
from src.domain.models import InvestigationEvidence


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceBoardService:
    def pin(
        self,
        state: InvestigationState,
        *,
        actor_id: UUID,
        fir_id: UUID | None = None,
        entity_id: UUID | None = None,
        note: str | None = None,
        tags: tuple[str, ...] = (),
        relevance_score: float = 1.0,
    ) -> InvestigationState:
        candidate = InvestigationEvidence(
            investigation_id=state.investigation_id,
            pinned_by=actor_id,
            fir_id=fir_id,
            entity_id=entity_id,
            note=note,
            tags=tags,
            relevance_score=relevance_score,
        )
        if any(item.fir_id == candidate.fir_id and item.entity_id == candidate.entity_id for item in state.evidence):
            return state
        return replace(state, evidence=state.evidence + (candidate,), updated_at=_now())

    def unpin(self, state: InvestigationState, *, fir_id: UUID | None = None, entity_id: UUID | None = None) -> InvestigationState:
        remaining = tuple(item for item in state.evidence if not (item.fir_id == fir_id and item.entity_id == entity_id))
        return replace(state, evidence=remaining, updated_at=_now())

    def add_note(self, state: InvestigationState, *, actor_id: UUID, text: str, tags: tuple[str, ...] = ()) -> InvestigationState:
        note = InvestigationNote(text=text, author_id=actor_id, note_id=uuid4(), tags=tags)
        return replace(state, notes=state.notes + (note,), updated_at=_now())


__all__ = ["EvidenceBoardService"]
