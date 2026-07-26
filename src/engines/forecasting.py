"""Bounded descriptive hotspot/forecast signals with explicit uncertainty."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .intelligence_types import EngineMetadata, SourceEvidence, Uncertainty

MAX_FORECAST_OBSERVATIONS = 500
MAX_FORECAST_KEYS = 100


@dataclass(frozen=True)
class ForecastObservation:
    observation_id: str
    key: str
    period: date
    count: int
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError("forecast count cannot be negative")


@dataclass(frozen=True)
class ForecastSignal:
    key: str
    observed_count: int
    baseline_count: float
    forecast_count: float
    trend: str
    interval: tuple[float, float]
    confidence: float
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class ForecastingResult:
    signals: tuple[ForecastSignal, ...]
    metadata: EngineMetadata
    uncertainty: Uncertainty


def forecast_hotspots(observations: Iterable[ForecastObservation], *, horizon: int = 1, max_observations: int = MAX_FORECAST_OBSERVATIONS) -> ForecastingResult:
    if not 1 <= horizon <= 7 or not 1 <= max_observations <= MAX_FORECAST_OBSERVATIONS:
        raise ValueError("forecast bounds are outside the permitted range")
    values = sorted(tuple(observations), key=lambda item: (item.period, item.observation_id))
    if len(values) > max_observations:
        raise ValueError("forecast input exceeds bounded observation limit")
    groups: dict[str, list[ForecastObservation]] = {}
    for value in values:
        groups.setdefault(value.key, []).append(value)
    if len(groups) > MAX_FORECAST_KEYS:
        raise ValueError("forecast input exceeds bounded key limit")
    signals: list[ForecastSignal] = []
    for key in sorted(groups):
        group = groups[key]
        counts = [item.count for item in group]
        baseline = sum(counts) / len(counts)
        slope = (counts[-1] - counts[0]) / max(1, len(counts) - 1)
        forecast = max(0.0, counts[-1] + slope * horizon)
        spread = max(counts) - min(counts) if counts else 0
        confidence = round(1 / (1 + spread / max(1, baseline)), 6) if counts else 0.0
        interval = (round(max(0.0, forecast - spread), 6), round(forecast + spread, 6))
        trend = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        signals.append(ForecastSignal(key, counts[-1], round(baseline, 6), round(forecast, 6), trend, interval, confidence, tuple(SourceEvidence(source) for source in sorted({source for item in group for source in item.source_ids}))))
    return ForecastingResult(tuple(signals), EngineMetadata("forecasting", "bounded_baseline_slope_signal", "p13.1", (("horizon", horizon), ("max_observations", max_observations)), len(values)), Uncertainty("historical_signal", 0.7 if values else 0.0, ("Forecast is a bounded signal with an interval, not guaranteed future conduct.",)))


__all__ = ["ForecastObservation", "ForecastSignal", "ForecastingResult", "forecast_hotspots"]
