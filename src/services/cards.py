"""Card materialization and immutable version lifecycle service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from src.adapters.card_store import CardStore
from src.domain.cards import CardPayload, CardProvenance, CardRecord, CardStatus


class CardService:
    """Materialize typed engine output into canonical versioned card records."""

    def __init__(self, store: CardStore, *, clock: Callable[[], datetime] | None = None) -> None:
        self.store = store
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def materialize(
        self,
        payload: CardPayload,
        *,
        provenance: CardProvenance,
        stale_after: datetime,
        card_id: str | None = None,
        generated_at: datetime | None = None,
    ) -> CardRecord:
        previous = self.store.get(card_id) if card_id else None
        record = CardRecord(
            card_id=card_id or _new_id(payload),
            version=(previous.version + 1 if previous else 1),
            generated_at=generated_at or self.clock(),
            stale_after=stale_after,
            payload=payload,
            provenance=provenance,
            supersedes_card_id=previous.card_id if previous else None,
        )
        if previous is not None:
            record = record.model_copy(update={"supersedes_card_id": previous.card_id})
        self.store.put(record)
        return record

    def get_current(self, card_id: str, *, at: datetime | None = None) -> CardRecord | None:
        current = self.store.get(card_id)
        return current.as_of(at) if current else None

    def mark_stale(self, card_id: str) -> CardRecord:
        current = self._required(card_id)
        stale = current.mark_stale()
        if stale.status != current.status:
            stale = stale.model_copy(update={"version": current.version + 1})
            self.store.put(stale)
        return stale

    def archive(self, card_id: str) -> CardRecord:
        current = self._required(card_id)
        archived = current.archive().model_copy(update={"version": current.version + 1})
        self.store.put(archived)
        return archived

    def historical_versions(self, card_id: str) -> tuple[CardRecord, ...]:
        return self.store.versions(card_id)

    def _required(self, card_id: str) -> CardRecord:
        value = self.store.get(card_id)
        if value is None:
            raise KeyError(f"card not found: {card_id}")
        return value


def _new_id(payload: CardPayload) -> str:
    subject = next((getattr(payload, name, None) for name in ("investigation_id", "entity_id", "lead_id", "trace_id", "alert_id", "card_type") if getattr(payload, name, None) is not None), payload.card_type.value)
    return f"{payload.card_type.value}:{subject}"


__all__ = ["CardService"]
