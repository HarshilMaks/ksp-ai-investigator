"""Local vector retrieval and optional backend fallback boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from src.shared.embedding import EmbeddingProvider, DeterministicEmbeddingProvider, cosine_similarity

from .types import Degradation, SearchDocument, VectorHit, VectorSearchResult

MAX_VECTOR_CANDIDATES = 100


class VectorBackendUnavailable(RuntimeError):
    """Raised by an optional external vector backend when it cannot serve a query."""


class ExternalVectorBackend(Protocol):
    def search(
        self,
        query: str,
        *,
        top_k: int,
        similarity_threshold: float,
        metadata_filter: Mapping[str, Any] | None,
    ) -> VectorSearchResult: ...


@dataclass(frozen=True)
class IndexedVector:
    document: SearchDocument
    vector: tuple[float, ...]


class LocalVectorIndex:
    """Small deterministic vector index for tests and offline development."""

    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        self.provider = provider or DeterministicEmbeddingProvider()
        self._documents: dict[tuple[str, str], IndexedVector] = {}

    def add(self, document: SearchDocument) -> None:
        vector = self.provider.embed(document.text)
        self._documents[(document.source_type, document.source_id)] = IndexedVector(document, vector)

    def add_many(self, documents: Sequence[SearchDocument]) -> None:
        for document in documents:
            self.add(document)

    def search(
        self,
        query: str,
        *,
        top_k: int = 20,
        similarity_threshold: float = 0.0,
        metadata_filter: Mapping[str, Any] | None = None,
    ) -> VectorSearchResult:
        _validate_limits(top_k, similarity_threshold)
        query_vector = self.provider.embed(query)
        scored: list[tuple[float, SearchDocument]] = []
        for indexed in self._documents.values():
            if not _matches_metadata(indexed.document.metadata, metadata_filter):
                continue
            score = cosine_similarity(query_vector, indexed.vector)
            if score >= similarity_threshold:
                scored.append((score, indexed.document))
        scored.sort(key=lambda item: (-item[0], item[1].source_id))
        hits = tuple(
            VectorHit(document=document, score=score, rank=rank)
            for rank, (score, document) in enumerate(scored[: min(top_k, MAX_VECTOR_CANDIDATES)], start=1)
        )
        return VectorSearchResult(hits=hits, backend="local-deterministic", degraded=False)


class VectorSearchService:
    """Prefer an injected pgvector-like backend, then degrade explicitly to local search."""

    def __init__(
        self,
        local_index: LocalVectorIndex,
        external_backend: ExternalVectorBackend | None = None,
    ) -> None:
        self.local_index = local_index
        self.external_backend = external_backend

    def search(
        self,
        query: str,
        *,
        top_k: int = 20,
        similarity_threshold: float = 0.0,
        metadata_filter: Mapping[str, Any] | None = None,
    ) -> VectorSearchResult:
        _validate_limits(top_k, similarity_threshold)
        if self.external_backend is not None:
            try:
                return self.external_backend.search(
                    query,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                    metadata_filter=metadata_filter,
                )
            except (VectorBackendUnavailable, ConnectionError, TimeoutError) as exc:
                local = self.local_index.search(
                    query,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                    metadata_filter=metadata_filter,
                )
                return VectorSearchResult(
                    hits=local.hits,
                    backend=local.backend,
                    degraded=True,
                    degradation=Degradation(
                        code="VECTOR_BACKEND_UNAVAILABLE",
                        message="External vector search unavailable; local deterministic search used.",
                        backend=type(self.external_backend).__name__,
                    ),
                )
        return self.local_index.search(
            query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            metadata_filter=metadata_filter,
        )


def _validate_limits(top_k: int, similarity_threshold: float) -> None:
    if isinstance(top_k, bool) or not 1 <= top_k <= MAX_VECTOR_CANDIDATES:
        raise ValueError(f"top_k must be between 1 and {MAX_VECTOR_CANDIDATES}")
    if not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError("similarity_threshold must be between 0 and 1")


def _matches_metadata(metadata: Mapping[str, Any], expected: Mapping[str, Any] | None) -> bool:
    if expected is None:
        return True
    return all(metadata.get(key) == value for key, value in expected.items())
