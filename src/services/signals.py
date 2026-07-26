"""Idempotent synthetic FIR signal ingestion and authorized matching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable


@dataclass(frozen=True)
class FIRSignal:
    event_id: str
    fir_id: str
    entity_ids: tuple[str, ...]
    summary: str
    source_ids: tuple[str, ...]
    observed_at: datetime


@dataclass(frozen=True)
class ActiveInvestigationMatch:
    investigation_id: str
    matched_entity_ids: tuple[str, ...]


@dataclass(frozen=True)
class IngestionResult:
    event_id: str
    fir_id: str
    duplicate: bool
    matches: tuple[ActiveInvestigationMatch, ...]


class SignalIngestionService:
    """Replay-safe FIR signal boundary; no broadcast or persistence platform."""

    def __init__(self, *, on_new_fir: Callable[[FIRSignal], None] | None = None) -> None:
        self._seen_events: set[str] = set()
        self._signals: dict[str, FIRSignal] = {}
        self._on_new_fir = on_new_fir

    def ingest(self, signal: FIRSignal, *, active_investigations: Iterable[tuple[str, frozenset[str]]] = ()) -> IngestionResult:
        if signal.event_id in self._seen_events:
            prior = self._signals[signal.event_id]
            return IngestionResult(prior.event_id, prior.fir_id, True, ())
        if not signal.source_ids or not signal.entity_ids:
            raise ValueError("a FIR signal requires source and entity references")
        self._seen_events.add(signal.event_id)
        self._signals[signal.event_id] = signal
        if self._on_new_fir:
            self._on_new_fir(signal)
        entity_set = set(signal.entity_ids)
        matches = tuple(ActiveInvestigationMatch(investigation_id, tuple(sorted(entity_set & set(watched)))) for investigation_id, watched in active_investigations if entity_set & set(watched))
        return IngestionResult(signal.event_id, signal.fir_id, False, matches)

    @property
    def signals(self) -> tuple[FIRSignal, ...]:
        return tuple(self._signals[key] for key in sorted(self._signals))


__all__ = ["ActiveInvestigationMatch", "FIRSignal", "IngestionResult", "SignalIngestionService"]
