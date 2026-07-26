"""First-class, approval-aware entity resolution for synthetic records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

LOCKED_EXACT_IDENTIFIER_TYPES = frozenset({"phone", "vehicle_registration", "bank_account", "upi_id"})


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


class ResolutionStatus(str, Enum):
    SUGGESTED = "suggested"
    AUTO_MERGED = "auto_merged"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ResolutionDecision:
    resolution_id: str
    entity_type: str
    entity_a_id: str
    entity_b_id: str
    confidence: float
    status: ResolutionStatus
    matched_identifiers: tuple[str, ...]
    officer_id: str | None = None


class EntityResolutionService:
    """Suggest matches; only exact locked identifiers can auto-merge."""

    def __init__(self) -> None:
        self._decisions: dict[str, ResolutionDecision] = {}
        self._merged: set[tuple[str, str]] = set()

    def resolve(
        self,
        *,
        resolution_id: str,
        entity_type: str,
        entity_a_id: str,
        entity_b_id: str,
        identifiers_a: dict[str, str],
        identifiers_b: dict[str, str],
    ) -> ResolutionDecision:
        matches = tuple(sorted(key for key in LOCKED_EXACT_IDENTIFIER_TYPES if key in identifiers_a and key in identifiers_b and normalize(identifiers_a[key]) == normalize(identifiers_b[key])))
        confidence = 1.0 if matches else round(sum(normalize(value) == normalize(identifiers_b.get(key, "")) for key, value in identifiers_a.items()) / max(1, len(identifiers_a)), 6)
        auto = bool(matches) and entity_type != "person"
        decision = ResolutionDecision(resolution_id, entity_type, entity_a_id, entity_b_id, confidence, ResolutionStatus.AUTO_MERGED if auto else ResolutionStatus.SUGGESTED, matches)
        self._decisions[resolution_id] = decision
        if auto:
            self._merged.add(tuple(sorted((entity_a_id, entity_b_id))))
        return decision

    def approve(self, resolution_id: str, *, officer_id: str) -> ResolutionDecision:
        decision = self._required(resolution_id)
        if not officer_id.strip():
            raise PermissionError("officer approval is required")
        if decision.status != ResolutionStatus.SUGGESTED:
            raise ValueError("only suggested resolutions can be approved")
        approved = ResolutionDecision(**{**decision.__dict__, "status": ResolutionStatus.APPROVED, "officer_id": officer_id})
        self._decisions[resolution_id] = approved
        self._merged.add(tuple(sorted((decision.entity_a_id, decision.entity_b_id))))
        return approved

    def reject(self, resolution_id: str, *, officer_id: str) -> ResolutionDecision:
        decision = self._required(resolution_id)
        if not officer_id.strip() or decision.status != ResolutionStatus.SUGGESTED:
            raise ValueError("only a pending suggestion can be rejected by an officer")
        rejected = ResolutionDecision(**{**decision.__dict__, "status": ResolutionStatus.REJECTED, "officer_id": officer_id})
        self._decisions[resolution_id] = rejected
        return rejected

    def is_merged(self, entity_a_id: str, entity_b_id: str) -> bool:
        return tuple(sorted((entity_a_id, entity_b_id))) in self._merged

    def _required(self, resolution_id: str) -> ResolutionDecision:
        if resolution_id not in self._decisions:
            raise KeyError(resolution_id)
        return self._decisions[resolution_id]


__all__ = ["EntityResolutionService", "LOCKED_EXACT_IDENTIFIER_TYPES", "ResolutionDecision", "ResolutionStatus", "normalize"]
