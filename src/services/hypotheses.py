"""Pure hypothesis mutations for the persistent investigation workspace."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain.investigation_state import Hypothesis, HypothesisStatus, InvestigationState


def _now() -> datetime:
    return datetime.now(timezone.utc)


class HypothesisService:
    def create(
        self,
        state: InvestigationState,
        *,
        actor_id: UUID,
        statement: str,
        supporting_evidence_ids: tuple[str, ...] = (),
        contradicting_evidence_ids: tuple[str, ...] = (),
        missing_critical_evidence: tuple[str, ...] = (),
        confidence: float = 0.0,
    ) -> InvestigationState:
        hypothesis = Hypothesis(
            statement=statement,
            created_by=actor_id,
            hypothesis_id=uuid4(),
            supporting_evidence_ids=supporting_evidence_ids,
            contradicting_evidence_ids=contradicting_evidence_ids,
            missing_critical_evidence=missing_critical_evidence,
            confidence=confidence,
        )
        return replace(state, hypotheses=state.hypotheses + (hypothesis,), updated_at=_now())

    def update(
        self,
        state: InvestigationState,
        *,
        hypothesis_id: UUID,
        status: HypothesisStatus | None = None,
        supporting_evidence_ids: tuple[str, ...] | None = None,
        contradicting_evidence_ids: tuple[str, ...] | None = None,
        missing_critical_evidence: tuple[str, ...] | None = None,
        confidence: float | None = None,
    ) -> InvestigationState:
        for index, current in enumerate(state.hypotheses):
            if current.hypothesis_id == hypothesis_id:
                updated = replace(
                    current,
                    status=current.status if status is None else status,
                    supporting_evidence_ids=current.supporting_evidence_ids if supporting_evidence_ids is None else supporting_evidence_ids,
                    contradicting_evidence_ids=current.contradicting_evidence_ids if contradicting_evidence_ids is None else contradicting_evidence_ids,
                    missing_critical_evidence=current.missing_critical_evidence if missing_critical_evidence is None else missing_critical_evidence,
                    confidence=current.confidence if confidence is None else confidence,
                    updated_at=_now(),
                )
                values = list(state.hypotheses)
                values[index] = updated
                return replace(state, hypotheses=tuple(values), updated_at=_now())
        raise KeyError(f"unknown hypothesis: {hypothesis_id}")


__all__ = ["HypothesisService"]
