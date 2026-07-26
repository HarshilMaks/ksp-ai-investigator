"""Deterministic modus-operandi and temporal pattern analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .intelligence_types import EngineMetadata, SourceEvidence, Uncertainty

MAX_PATTERN_EVENTS = 500


@dataclass(frozen=True)
class PatternEvent:
    event_id: str
    subject_id: str
    occurred_at: datetime
    category: str
    location_id: str | None = None
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModusOperandiSignal:
    subject_id: str
    dominant_categories: tuple[str, ...]
    event_count: int
    repeat_rate: float
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class TemporalPatternSignal:
    subject_id: str
    hour_buckets: tuple[tuple[int, int], ...]
    median_gap_hours: float | None
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class PatternAnalysisResult:
    modus_operandi: tuple[ModusOperandiSignal, ...]
    temporal: tuple[TemporalPatternSignal, ...]
    metadata: EngineMetadata
    uncertainty: Uncertainty


def analyze_patterns(events: Iterable[PatternEvent], *, max_events: int = MAX_PATTERN_EVENTS) -> PatternAnalysisResult:
    if not 1 <= max_events <= MAX_PATTERN_EVENTS:
        raise ValueError(f"max_events must be between 1 and {MAX_PATTERN_EVENTS}")
    ordered = sorted(tuple(events), key=lambda event: (event.occurred_at, event.event_id))
    if len(ordered) > max_events:
        raise ValueError("pattern input exceeds bounded event limit")
    grouped: dict[str, list[PatternEvent]] = defaultdict(list)
    for event in ordered:
        grouped[event.subject_id].append(event)
    mo: list[ModusOperandiSignal] = []
    temporal: list[TemporalPatternSignal] = []
    for subject_id in sorted(grouped):
        subject_events = grouped[subject_id]
        categories = Counter(event.category for event in subject_events)
        repeated = sum(count - 1 for count in categories.values() if count > 1)
        evidence = _sources(subject_events)
        mo.append(ModusOperandiSignal(subject_id, tuple(category for category, _ in categories.most_common()), len(subject_events), round(repeated / max(1, len(subject_events)), 6), evidence))
        hours = Counter(event.occurred_at.hour for event in subject_events)
        gaps = tuple((right.occurred_at - left.occurred_at).total_seconds() / 3600 for left, right in zip(subject_events, subject_events[1:]))
        temporal.append(TemporalPatternSignal(subject_id, tuple(sorted(hours.items())), round(sum(gaps) / len(gaps), 6) if gaps else None, evidence))
    return PatternAnalysisResult(tuple(mo), tuple(temporal), EngineMetadata("pattern_analysis", "category_repeat_and_temporal_gaps", "p13.1", (("max_events", max_events),), len(ordered)), Uncertainty("observed_event_history", 1.0 if ordered else 0.0, ("Patterns describe observed records and do not establish intent.",)))


def _sources(events: Iterable[PatternEvent]) -> tuple[SourceEvidence, ...]:
    return tuple(SourceEvidence(source_id) for source_id in sorted({source for event in events for source in event.source_ids}))


__all__ = ["ModusOperandiSignal", "PatternAnalysisResult", "PatternEvent", "TemporalPatternSignal", "analyze_patterns"]
