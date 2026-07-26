"""Canonical JSON, metadata-index, and hot-cache card storage boundaries."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from src.domain.cards import CardRecord, CardStatus, CardType


class CardStore(Protocol):
    def put(self, card: CardRecord) -> None: ...
    def get(self, card_id: str, version: int | None = None) -> CardRecord | None: ...
    def versions(self, card_id: str) -> tuple[CardRecord, ...]: ...
    def list_metadata(self, *, investigation_id: str | None = None, card_type: CardType | None = None) -> tuple[dict[str, object], ...]: ...


class InMemoryCardStore:
    """Local test/cache implementation with immutable historical versions."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, int], CardRecord] = {}
        self._cache: dict[str, CardRecord] = {}

    def put(self, card: CardRecord) -> None:
        key = (card.card_id, card.version)
        if key in self._records:
            raise ValueError("card version already exists")
        latest = self.get(card.card_id)
        if latest is not None and card.version <= latest.version:
            raise ValueError("card version must increase monotonically")
        self._records[key] = card
        self._cache[card.card_id] = card

    def get(self, card_id: str, version: int | None = None) -> CardRecord | None:
        if version is None:
            return self._cache.get(card_id)
        return self._records.get((card_id, version))

    def versions(self, card_id: str) -> tuple[CardRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records) if key[0] == card_id)

    def list_metadata(self, *, investigation_id: str | None = None, card_type: CardType | None = None) -> tuple[dict[str, object], ...]:
        records = []
        for card in self._cache.values():
            payload = card.payload
            if investigation_id is not None and getattr(payload, "investigation_id", None) != investigation_id:
                continue
            if card_type is not None and payload.card_type != card_type:
                continue
            records.append({"card_id": card.card_id, "card_type": payload.card_type.value, "version": card.version, "status": card.status.value, "generated_at": card.generated_at.isoformat(), "confidence": _confidence(payload)})
        return tuple(sorted(records, key=lambda item: str(item["card_id"])))


class LocalCardStore(InMemoryCardStore):
    """Atomic local canonical JSON store mirroring the Stratus/index/cache flow."""

    def __init__(self, root: str | Path) -> None:
        super().__init__()
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "metadata-index.json"
        self._load()

    def put(self, card: CardRecord) -> None:
        super().put(card)
        path = self.root / card.card_id / f"v{card.version}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(card.model_dump(mode="json"), sort_keys=True), encoding="utf-8")
        os.replace(temporary, path)
        self._write_index()

    def _load(self) -> None:
        for path in sorted(self.root.glob("*/v*.json")):
            try:
                card = CardRecord.model_validate_json(path.read_text(encoding="utf-8"))
                self._records[(card.card_id, card.version)] = card
                if self._cache.get(card.card_id) is None or self._cache[card.card_id].version < card.version:
                    self._cache[card.card_id] = card
            except (OSError, ValueError):
                continue

    def _write_index(self) -> None:
        temporary = self.index_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(list(self.list_metadata()), sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.index_path)


def _confidence(payload: object) -> float | None:
    for name in ("confidence_score", "confidence", "overall_confidence", "conclusion_confidence"):
        value = getattr(payload, name, None)
        if value is not None:
            return float(value)
    return None


__all__ = ["CardStore", "InMemoryCardStore", "LocalCardStore"]
