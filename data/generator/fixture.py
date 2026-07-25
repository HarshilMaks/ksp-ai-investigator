"""Synthetic fixture bundle and reproducibility helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from src.domain.models import Entity, FIR, FIREntityLink, Relationship, to_record

from .fir_generator import generate_firs
from .network_generator import generate_network_records


@dataclass(frozen=True)
class SyntheticFixture:
    firs: tuple[FIR, ...]
    entities: tuple[Entity, ...]
    fir_entities: tuple[FIREntityLink, ...]
    relationships: tuple[Relationship, ...]

    def to_record(self) -> dict[str, Any]:
        return to_record(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_record(), sort_keys=True, separators=(",", ":"))

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def generate_fixture(count: int = 10, *, seed: int = 20260725, year: int = 2026) -> SyntheticFixture:
    firs = generate_firs(count=count, seed=seed, year=year)
    entities, links, relationships = generate_network_records(firs, seed=seed)
    return SyntheticFixture(tuple(firs), tuple(entities), tuple(links), tuple(relationships))
