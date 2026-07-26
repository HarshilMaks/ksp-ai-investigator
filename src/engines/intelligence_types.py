"""Typed provenance and computation metadata shared by P13 engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

ParameterValue: TypeAlias = str | int | float | bool


@dataclass(frozen=True)
class SourceEvidence:
    source_id: str
    source_type: str = "record"
    locator: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.source_type.strip():
            raise ValueError("source evidence requires source_id and source_type")


@dataclass(frozen=True)
class EngineMetadata:
    engine: str
    algorithm: str
    version: str
    parameters: tuple[tuple[str, ParameterValue], ...]
    input_count: int
    bounded: bool = True

    def __post_init__(self) -> None:
        if not self.engine.strip() or not self.algorithm.strip() or not self.version.strip():
            raise ValueError("engine metadata requires engine, algorithm, and version")
        if self.input_count < 0 or not self.bounded:
            raise ValueError("engine metadata must describe a bounded non-negative computation")


@dataclass(frozen=True)
class Uncertainty:
    kind: str
    confidence: float
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("uncertainty confidence must be between 0 and 1")
        if not self.kind.strip():
            raise ValueError("uncertainty kind is required")


__all__ = ["EngineMetadata", "ParameterValue", "SourceEvidence", "Uncertainty"]
