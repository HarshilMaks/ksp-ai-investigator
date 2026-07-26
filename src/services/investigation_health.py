"""Deterministic Investigation Health calculation for P09."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from src.domain.investigation_state import HealthProvenance, InvestigationHealth, InvestigationState
from src.domain.enums import TimelineEventType


class InvestigationHealthService:
    """Compute repeatable coverage signals from the persisted investigation state."""

    evidence_target = 5
    timeline_target = 5
    network_target = 6

    def calculate(self, state: InvestigationState) -> InvestigationHealth:
        evidence_ids = tuple(self._evidence_ids(state))
        timeline_ids = tuple(str(event.timeline_id) for event in state.timeline)
        entity_ids = {str(item.entity_id) for item in state.evidence if item.entity_id is not None}
        network_signal = len(entity_ids) + (1 if len(entity_ids) > 1 else 0)
        financial_ids = tuple(
            source_id
            for item in state.evidence
            if any(tag.lower() in {"financial", "bank", "account", "upi", "transaction"} for tag in item.tags)
            for source_id in self._evidence_item_ids(item)
        )
        witness_ids = tuple(
            source_id
            for item in state.evidence
            if any(tag.lower() in {"witness", "witness_statement"} for tag in item.tags)
            for source_id in self._evidence_item_ids(item)
        )
        witness_ids += tuple(
            timeline_id for event, timeline_id in zip(state.timeline, timeline_ids) if event.event_type == TimelineEventType.WITNESS_STATEMENT
        )
        contradiction_ids = tuple(
            sorted({evidence_id for hypothesis in state.hypotheses for evidence_id in hypothesis.contradicting_evidence_ids})
        )
        missing: list[str] = []
        if not evidence_ids:
            missing.append("pinned evidence")
        if not timeline_ids:
            missing.append("timeline events")
        if network_signal < 2:
            missing.append("network relationships")
        if not financial_ids:
            missing.append("financial records")
        if not witness_ids:
            missing.append("witness statement")
        return InvestigationHealth(
            evidence_coverage=min(1.0, len(evidence_ids) / self.evidence_target),
            timeline_completeness=min(1.0, len(timeline_ids) / self.timeline_target),
            network_coverage=min(1.0, network_signal / self.network_target),
            financial_coverage=min(1.0, len(set(financial_ids))),
            witness_coverage=min(1.0, len(set(witness_ids))),
            contradiction_count=len(contradiction_ids),
            missing_critical_evidence=tuple(missing),
            provenance=(
                HealthProvenance("evidence_coverage", evidence_ids, f"unique pinned evidence sources / {self.evidence_target}"),
                HealthProvenance("timeline_completeness", timeline_ids, f"timeline events / {self.timeline_target}"),
                HealthProvenance("network_coverage", tuple(sorted(entity_ids)), f"unique evidence entities plus relationship signal / {self.network_target}"),
                HealthProvenance("financial_coverage", tuple(sorted(set(financial_ids))), "1.0 when at least one financial-tagged source exists"),
                HealthProvenance("witness_coverage", tuple(sorted(set(witness_ids))), "1.0 when a witness-tagged source or witness event exists"),
                HealthProvenance("contradictions", contradiction_ids, "unique evidence IDs marked contradictory by hypotheses"),
            ),
        )

    @staticmethod
    def _evidence_item_ids(item: object) -> tuple[str, ...]:
        ids: list[str] = []
        fir_id = getattr(item, "fir_id", None)
        entity_id = getattr(item, "entity_id", None)
        if fir_id is not None:
            ids.append(f"fir:{fir_id}")
        if entity_id is not None:
            ids.append(f"entity:{entity_id}")
        return tuple(ids)

    def _evidence_ids(self, state: InvestigationState) -> Iterable[str]:
        seen: set[str] = set()
        for item in state.evidence:
            for value in self._evidence_item_ids(item):
                if value not in seen:
                    seen.add(value)
                    yield value


__all__ = ["InvestigationHealthService"]
