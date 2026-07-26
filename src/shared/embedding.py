"""Embedding boundaries with a deterministic offline implementation.

The production embedding model remains an adapter concern. This local provider
makes retrieval reproducible without downloading a model or calling a service.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, Sequence

TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)


class EmbeddingProvider(Protocol):
    dimensions: int

    def embed(self, text: str) -> tuple[float, ...]: ...


class EmbeddingUnavailable(RuntimeError):
    """An external embedding backend cannot serve the request."""


class DeterministicEmbeddingProvider:
    """Hashing-based normalized embeddings for deterministic local retrieval."""

    def __init__(self, dimensions: int = 1024, *, namespace: str = "ksp-local-bge-m3") -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions
        self.namespace = namespace

    def embed(self, text: str) -> tuple[float, ...]:
        tokens = TOKEN_PATTERN.findall(text.lower())
        vector = [0.0] * self.dimensions
        for position, token in enumerate(tokens):
            digest = hashlib.sha256(f"{self.namespace}:{position}:{token}".encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            magnitude = 0.5 + (digest[5] / 255.0)
            vector[index] += sign * magnitude
        return _normalize(vector)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have equal dimensions")
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
    if denominator == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / denominator


def _normalize(vector: list[float]) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return tuple(vector)
    return tuple(value / norm for value in vector)
