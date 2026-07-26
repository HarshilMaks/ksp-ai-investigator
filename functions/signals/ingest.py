"""Thin Catalyst signal delegates; business behavior remains in src/services."""

from src.services.signals import FIRSignal, IngestionResult, SignalIngestionService


def ingest_signal(service: SignalIngestionService, signal: FIRSignal, *, active_investigations=()) -> IngestionResult:
    return service.ingest(signal, active_investigations=active_investigations)


__all__ = ["FIRSignal", "IngestionResult", "SignalIngestionService", "ingest_signal"]
