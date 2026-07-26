"""Shared deterministic retrieval contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RetrievalCitation:
    source_type: str
    source_id: str
    locator: str | None = None


@dataclass(frozen=True)
class SearchDocument:
    source_type: str
    source_id: str
    text: str
    record: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    citation: RetrievalCitation | None = None


@dataclass(frozen=True)
class VectorHit:
    document: SearchDocument
    score: float
    rank: int


@dataclass(frozen=True)
class LexicalHit:
    document: SearchDocument
    score: float
    rank: int


@dataclass(frozen=True)
class HybridHit:
    document: SearchDocument
    score: float
    rank: int
    lexical_score: float | None
    vector_score: float | None
    lexical_rank: int | None
    vector_rank: int | None
    citation: RetrievalCitation


@dataclass(frozen=True)
class Degradation:
    code: str
    message: str
    backend: str


@dataclass(frozen=True)
class VectorSearchResult:
    hits: tuple[VectorHit, ...]
    backend: str
    degraded: bool = False
    degradation: Degradation | None = None


@dataclass(frozen=True)
class HybridSearchResult:
    hits: tuple[HybridHit, ...]
    backend: str
    rrf_k: int
    candidate_count: int
    degraded: bool = False
    degradation: Degradation | None = None


@dataclass(frozen=True)
class StructuredRecord:
    record: dict[str, Any]
    rank: int
    citation: RetrievalCitation


@dataclass(frozen=True)
class StructuredQueryResult:
    records: tuple[StructuredRecord, ...]
    total: int
    filters_applied: dict[str, Any]
    degraded: bool = False
