"""Deterministic, review-oriented lead ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .intelligence_types import EngineMetadata, SourceEvidence, Uncertainty

MAX_LEADS = 200


@dataclass(frozen=True)
class LeadCandidate:
    lead_id: str
    title: str
    actionability: float
    urgency: float
    evidence_strength: float
    missing_evidence: int = 0
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value in (self.actionability, self.urgency, self.evidence_strength):
            if not 0.0 <= value <= 1.0:
                raise ValueError("lead factors must be between 0 and 1")
        if self.missing_evidence < 0:
            raise ValueError("missing evidence count cannot be negative")


@dataclass(frozen=True)
class RankedLead:
    lead_id: str
    title: str
    score: float
    rank: int
    review_reasons: tuple[str, ...]
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class LeadRankingResult:
    leads: tuple[RankedLead, ...]
    metadata: EngineMetadata
    uncertainty: Uncertainty


def rank_leads(candidates: Iterable[LeadCandidate], *, max_leads: int = MAX_LEADS) -> LeadRankingResult:
    if not 1 <= max_leads <= MAX_LEADS:
        raise ValueError(f"max_leads must be between 1 and {MAX_LEADS}")
    values = tuple(candidates)
    if len(values) > max_leads:
        raise ValueError("lead input exceeds bounded candidate limit")
    scored = []
    for candidate in values:
        score = round(0.4 * candidate.actionability + 0.3 * candidate.urgency + 0.3 * candidate.evidence_strength - min(0.2, candidate.missing_evidence * 0.02), 6)
        reasons = tuple(reason for reason, condition in (("actionable next step", candidate.actionability >= 0.5), ("time-sensitive", candidate.urgency >= 0.5), ("source-supported", candidate.evidence_strength >= 0.5), ("missing evidence remains", candidate.missing_evidence > 0)) if condition)
        scored.append((score, candidate, reasons))
    scored.sort(key=lambda item: (-item[0], item[1].lead_id))
    leads = tuple(RankedLead(candidate.lead_id, candidate.title, score, index, reasons, tuple(SourceEvidence(source) for source in sorted(candidate.source_ids))) for index, (score, candidate, reasons) in enumerate(scored, 1))
    return LeadRankingResult(leads, EngineMetadata("lead_ranking", "weighted_review_priority", "p13.1", (("max_leads", max_leads),), len(values)), Uncertainty("evidence_supported_priority", 1.0 if values else 0.0, ("Ranking prioritizes review; it does not determine guilt or legal sufficiency.",)))


__all__ = ["LeadCandidate", "LeadRankingResult", "RankedLead", "rank_leads"]
