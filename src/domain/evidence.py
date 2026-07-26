"""Evidence-gate domain contracts.

These records contain structured rationale, provenance, uncertainty, and audit
metadata. They never store or expose private chain-of-thought.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.shared.clock import isoformat_utc


@dataclass(frozen=True)
class EvidenceClaim:
    claim_id: str
    text: str
    source_ids: tuple[str, ...]
    confidence: float = 1.0
    uncertainty: Mapping[str, Any] = field(default_factory=dict)
    contradiction_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.claim_id.strip() or not self.text.strip():
            raise ValueError("claim_id and text are required")
        if not self.source_ids:
            raise ValueError("every released claim must have at least one source")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class EvidenceAuditMetadata:
    request_id: str
    officer_id: str
    tool_id: str
    route: str = "fast"
    checked_at: str = field(default_factory=isoformat_utc)
    source_count: int = 0
    claim_count: int = 0


@dataclass(frozen=True)
class EvidenceDecision:
    released: bool
    claims: tuple[EvidenceClaim, ...]
    citations: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    uncertainty: Mapping[str, Any]
    audit: EvidenceAuditMetadata

    @property
    def source_coverage(self) -> float:
        if not self.claims:
            return 1.0 if not self.errors else 0.0
        covered = sum(1 for claim in self.claims if claim.source_ids)
        return covered / len(self.claims)
