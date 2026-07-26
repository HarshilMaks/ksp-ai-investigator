"""Deterministic timeline reconstruction from timestamped source events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .intelligence_types import EngineMetadata, SourceEvidence, Uncertainty

MAX_TIMELINE_EVENTS = 500


@dataclass(frozen=True)
class TimelineInput:
    event_id: str
    occurred_at: datetime
    label: str
    entity_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("timeline confidence must be between 0 and 1")


@dataclass(frozen=True)
class ReconstructedTimelineEvent:
    sequence: int
    event_id: str
    occurred_at: datetime
    label: str
    entity_ids: tuple[str, ...]
    confidence: float
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class TimelineGap:
    before_event_id: str
    after_event_id: str
    duration_hours: float


@dataclass(frozen=True)
class TimelineResult:
    events: tuple[ReconstructedTimelineEvent, ...]
    gaps: tuple[TimelineGap, ...]
    metadata: EngineMetadata
    uncertainty: Uncertainty


def reconstruct_timeline(events: Iterable[TimelineInput], *, gap_threshold_hours: float = 24.0, max_events: int = MAX_TIMELINE_EVENTS) -> TimelineResult:
    if gap_threshold_hours <= 0 or not 1 <= max_events <= MAX_TIMELINE_EVENTS:
        raise ValueError("timeline bounds are invalid")
    values = sorted(tuple(events), key=lambda item: (item.occurred_at, item.event_id))
    if len(values) > max_events:
        raise ValueError("timeline input exceeds bounded event limit")
    reconstructed = tuple(ReconstructedTimelineEvent(index, item.event_id, item.occurred_at, item.label, tuple(sorted(item.entity_ids)), item.confidence, tuple(SourceEvidence(source) for source in sorted(item.source_ids))) for index, item in enumerate(values, 1))
    gaps = tuple(TimelineGap(left.event_id, right.event_id, round((right.occurred_at - left.occurred_at).total_seconds() / 3600, 6)) for left, right in zip(reconstructed, reconstructed[1:]) if (right.occurred_at - left.occurred_at).total_seconds() / 3600 > gap_threshold_hours)
    return TimelineResult(reconstructed, gaps, EngineMetadata("timeline", "stable_timestamp_sort_and_gap_detection", "p13.1", (("gap_threshold_hours", gap_threshold_hours), ("max_events", max_events)), len(values)), Uncertainty("timestamp_completeness", round(sum(item.confidence for item in values) / len(values), 6) if values else 0.0, ("Ordering follows supplied timestamps; missing events remain unknown.",)))


__all__ = ["ReconstructedTimelineEvent", "TimelineGap", "TimelineInput", "TimelineResult", "reconstruct_timeline"]
