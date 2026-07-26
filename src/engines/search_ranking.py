"""Deterministic lexical, vector, and hybrid retrieval ranking."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from src.domain.models import FIR, to_record
from src.shared.embedding import DeterministicEmbeddingProvider, EmbeddingProvider

from .retrieval.types import (
    HybridHit,
    HybridSearchResult,
    LexicalHit,
    RetrievalCitation,
    SearchDocument,
)
from .retrieval.vector import ExternalVectorBackend, LocalVectorIndex, VectorSearchService

TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)
RRF_K = 60
MAX_SEARCH_CANDIDATES = 100


@dataclass(frozen=True)
class LexicalIndex:
    documents: tuple[SearchDocument, ...]

    def search(
        self,
        query: str,
        *,
        top_k: int = MAX_SEARCH_CANDIDATES,
        metadata_filter: Mapping[str, Any] | None = None,
    ) -> tuple[LexicalHit, ...]:
        if not 1 <= top_k <= MAX_SEARCH_CANDIDATES:
            raise ValueError(f"top_k must be between 1 and {MAX_SEARCH_CANDIDATES}")
        query_tokens = _tokens(query)
        if not query_tokens:
            return ()
        candidate_docs = [
            document for document in self.documents if _matches_metadata(document.metadata, metadata_filter)
        ]
        tokenized = {document.source_id: _tokens(document.text) for document in candidate_docs}
        document_frequency = Counter(
            token for values in tokenized.values() for token in set(values)
        )
        average_length = sum(len(values) for values in tokenized.values()) / max(len(tokenized), 1)
        scored: list[tuple[float, SearchDocument]] = []
        for document in candidate_docs:
            values = tokenized[document.source_id]
            score = _bm25(query_tokens, values, document_frequency, len(candidate_docs), average_length)
            if score > 0:
                scored.append((score, document))
        scored.sort(key=lambda item: (-item[0], item[1].source_id))
        return tuple(
            LexicalHit(document=document, score=score, rank=rank)
            for rank, (score, document) in enumerate(scored[:top_k], start=1)
        )


class DeterministicReranker:
    """Stable reranking boundary; no model call or learned claim is made."""

    def rerank(self, hits: Sequence[HybridHit], *, limit: int) -> tuple[HybridHit, ...]:
        if not 1 <= limit <= MAX_SEARCH_CANDIDATES:
            raise ValueError(f"limit must be between 1 and {MAX_SEARCH_CANDIDATES}")
        ordered = sorted(
            hits,
            key=lambda hit: (
                -hit.score,
                -(hit.vector_score or 0.0),
                -(hit.lexical_score or 0.0),
                hit.document.source_id,
            ),
        )
        return tuple(
            HybridHit(
                document=hit.document,
                score=hit.score,
                rank=rank,
                lexical_score=hit.lexical_score,
                vector_score=hit.vector_score,
                lexical_rank=hit.lexical_rank,
                vector_rank=hit.vector_rank,
                citation=hit.citation,
            )
            for rank, hit in enumerate(ordered[:limit], start=1)
        )


class HybridSearchEngine:
    """Search FIR narratives with lexical/vector retrieval and explicit degradation."""

    def __init__(
        self,
        documents: Sequence[SearchDocument],
        *,
        embedding_provider: EmbeddingProvider | None = None,
        external_vector_backend: ExternalVectorBackend | None = None,
        rrf_k: int = RRF_K,
    ) -> None:
        if rrf_k < 1:
            raise ValueError("rrf_k must be positive")
        self.documents = tuple(documents)
        self.lexical = LexicalIndex(self.documents)
        self.vector = VectorSearchService(
            LocalVectorIndex(embedding_provider or DeterministicEmbeddingProvider()),
            external_backend=external_vector_backend,
        )
        self.vector.local_index.add_many(self.documents)
        self.rrf_k = rrf_k
        self.reranker = DeterministicReranker()

    @classmethod
    def from_firs(
        cls,
        firs: Iterable[FIR],
        *,
        embedding_provider: EmbeddingProvider | None = None,
        external_vector_backend: ExternalVectorBackend | None = None,
    ) -> "HybridSearchEngine":
        documents = []
        for fir in firs:
            record = to_record(fir)
            mo = fir.modus_operandi.get("method", "")
            text = " ".join(
                value for value in (fir.narrative_en or "", fir.crime_category, fir.district, str(mo)) if value
            )
            documents.append(
                SearchDocument(
                    source_type="FIR",
                    source_id=str(fir.fir_id),
                    text=text,
                    record=record,
                    metadata={
                        "district": fir.district,
                        "crime_category": fir.crime_category,
                        "ps_code": fir.ps_code,
                        "year": fir.registration_date.year,
                    },
                    citation=RetrievalCitation(source_type="FIR", source_id=str(fir.fir_id)),
                )
            )
        return cls(
            documents,
            embedding_provider=embedding_provider,
            external_vector_backend=external_vector_backend,
        )

    def search(
        self,
        query: str,
        *,
        top_k: int = 20,
        similarity_threshold: float = 0.0,
        metadata_filter: Mapping[str, Any] | None = None,
    ) -> HybridSearchResult:
        if not query.strip():
            raise ValueError("query must be non-empty")
        if not 1 <= top_k <= MAX_SEARCH_CANDIDATES:
            raise ValueError(f"top_k must be between 1 and {MAX_SEARCH_CANDIDATES}")
        candidate_limit = MAX_SEARCH_CANDIDATES
        lexical_hits = self.lexical.search(query, top_k=candidate_limit, metadata_filter=metadata_filter)
        vector_result = self.vector.search(
            query,
            top_k=candidate_limit,
            similarity_threshold=similarity_threshold,
            metadata_filter=metadata_filter,
        )
        lexical_by_id = {hit.document.source_id: hit for hit in lexical_hits}
        vector_by_id = {hit.document.source_id: hit for hit in vector_result.hits}
        candidate_ids = sorted(set(lexical_by_id) | set(vector_by_id))
        fused: list[HybridHit] = []
        for source_id in candidate_ids:
            lexical_hit = lexical_by_id.get(source_id)
            vector_hit = vector_by_id.get(source_id)
            score = 0.0
            if lexical_hit:
                score += 1.0 / (self.rrf_k + lexical_hit.rank)
            if vector_hit:
                score += 1.0 / (self.rrf_k + vector_hit.rank)
            document = lexical_hit.document if lexical_hit else vector_hit.document
            citation = document.citation or RetrievalCitation(document.source_type, document.source_id)
            fused.append(
                HybridHit(
                    document=document,
                    score=score,
                    rank=0,
                    lexical_score=lexical_hit.score if lexical_hit else None,
                    vector_score=vector_hit.score if vector_hit else None,
                    lexical_rank=lexical_hit.rank if lexical_hit else None,
                    vector_rank=vector_hit.rank if vector_hit else None,
                    citation=citation,
                )
            )
        ranked = self.reranker.rerank(fused, limit=top_k)
        return HybridSearchResult(
            hits=ranked,
            backend=vector_result.backend,
            rrf_k=self.rrf_k,
            candidate_count=len(candidate_ids),
            degraded=vector_result.degraded,
            degradation=vector_result.degradation,
        )


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _bm25(
    query_tokens: Sequence[str],
    document_tokens: Sequence[str],
    document_frequency: Counter[str],
    document_count: int,
    average_length: float,
) -> float:
    if not document_tokens:
        return 0.0
    counts = Counter(document_tokens)
    length = len(document_tokens)
    score = 0.0
    for token in query_tokens:
        term_frequency = counts[token]
        if term_frequency == 0:
            continue
        frequency = document_frequency[token]
        inverse_document_frequency = math.log(1.0 + (document_count - frequency + 0.5) / (frequency + 0.5))
        denominator = term_frequency + 1.5 * (1.0 - 0.75 + 0.75 * length / max(average_length, 1.0))
        score += inverse_document_frequency * term_frequency * 2.5 / denominator
    return score


def _matches_metadata(metadata: Mapping[str, Any], expected: Mapping[str, Any] | None) -> bool:
    if expected is None:
        return True
    return all(metadata.get(key) == value for key, value in expected.items())
