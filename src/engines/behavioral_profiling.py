"""Deterministic behavioral profile features over observed events."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .intelligence_types import EngineMetadata, SourceEvidence, Uncertainty

MAX_BEHAVIOR_EVENTS = 500


@dataclass(frozen=True)
class BehavioralEvent:
    event_id: str
    subject_id: str
    occurred_at: datetime
    category: str
    severity: float
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("severity must be between 0 and 1")


@dataclass(frozen=True)
class BehavioralProfile:
    subject_id: str
    category_counts: tuple[tuple[str, int], ...]
    active_hours: tuple[tuple[int, int], ...]
    average_severity: float
    severity_direction: str
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class BehavioralProfilingResult:
    profiles: tuple[BehavioralProfile, ...]
    metadata: EngineMetadata
    uncertainty: Uncertainty


def profile_behavior(events: Iterable[BehavioralEvent], *, max_events: int = MAX_BEHAVIOR_EVENTS) -> BehavioralProfilingResult:
    if not 1 <= max_events <= MAX_BEHAVIOR_EVENTS:
        raise ValueError(f"max_events must be between 1 and {MAX_BEHAVIOR_EVENTS}")
    ordered = sorted(tuple(events), key=lambda event: (event.occurred_at, event.event_id))
    if len(ordered) > max_events:
        raise ValueError("behavior input exceeds bounded event limit")
    grouped: dict[str, list[BehavioralEvent]] = defaultdict(list)
    for event in ordered:
        grouped[event.subject_id].append(event)
    profiles: list[BehavioralProfile] = []
    for subject_id in sorted(grouped):
        subject = grouped[subject_id]
        severities = [event.severity for event in subject]
        midpoint = max(1, len(severities) // 2)
        first, second = sum(severities[:midpoint]) / midpoint, sum(severities[midpoint:]) / max(1, len(severities[midpoint:]))
        direction = "increasing" if second > first else "decreasing" if second < first else "stable"
        profiles.append(BehavioralProfile(subject_id, tuple(sorted(Counter(event.category for event in subject).items())), tuple(sorted(Counter(event.occurred_at.hour for event in subject).items())), round(sum(severities) / len(severities), 6), direction, tuple(SourceEvidence(source) for source in sorted({source for event in subject for source in event.source_ids}))))
    return BehavioralProfilingResult(tuple(profiles), EngineMetadata("behavioral_profiling", "observed_frequency_and_severity_features", "p13.1", (("max_events", max_events),), len(ordered)), Uncertainty("partial_observation", 0.8 if ordered else 0.0, ("Behavioral features are descriptive, not a prediction of conduct.",)))


__all__ = ["BehavioralEvent", "BehavioralProfile", "BehavioralProfilingResult", "profile_behavior"]
