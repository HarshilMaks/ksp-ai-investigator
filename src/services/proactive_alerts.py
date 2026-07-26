"""Authorized proactive alert lifecycle over P14 card storage."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.adapters.card_store import CardStore
from src.domain.cards import CardProvenance, CardStatus, ProactiveAlertCard
from src.registry.tools import AuthorizationContext

from .cards import CardService
from .signals import FIRSignal


class ProactiveAlertService:
    def __init__(self, store: CardStore, *, clock=None, ttl: timedelta = timedelta(hours=48)) -> None:
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.ttl = ttl
        self.cards = CardService(store, clock=self.clock)
        self._alerts: dict[str, tuple[str, datetime]] = {}

    def create_for_match(self, signal: FIRSignal, *, investigation_id: str, authorization: AuthorizationContext) -> ProactiveAlertCard:
        self._authorize(investigation_id, authorization)
        now = self.clock()
        alert_id = f"alert:{signal.event_id}:{investigation_id}"
        payload = ProactiveAlertCard(
            alert_id=alert_id,
            investigation_id=investigation_id,
            what_changed=f"New FIR signal {signal.fir_id} linked to watched entities.",
            why_it_matters=signal.summary,
            confidence=1.0,
            urgency="high",
            status="new",
        )
        card = self.cards.materialize(payload, card_id=alert_id, generated_at=now, stale_after=now + self.ttl, provenance=CardProvenance(engine="signals_pipeline", algorithm_version="p15.1", source_ids=signal.source_ids, data_snapshot=signal.observed_at.isoformat()))
        self._alerts[alert_id] = (investigation_id, now + self.ttl)
        return card

    def acknowledge(self, alert_id: str, *, officer_id: str, authorization: AuthorizationContext) -> ProactiveAlertCard:
        investigation_id, _ = self._required(alert_id)
        self._authorize(investigation_id, authorization)
        current = self.cards.get_current(alert_id)
        assert current is not None
        payload = current.payload
        if not isinstance(payload, ProactiveAlertCard):
            raise TypeError("alert card payload is invalid")
        updated = payload.model_copy(update={"status": "acknowledged"})
        return self.cards.materialize(updated, card_id=alert_id, generated_at=self.clock(), stale_after=current.stale_after, provenance=current.provenance)

    def expire(self, alert_id: str, *, authorization: AuthorizationContext) -> ProactiveAlertCard:
        investigation_id, _ = self._required(alert_id)
        self._authorize(investigation_id, authorization)
        current = self.cards.get_current(alert_id)
        assert current is not None
        payload = current.payload
        if not isinstance(payload, ProactiveAlertCard):
            raise TypeError("alert card payload is invalid")
        updated = payload.model_copy(update={"status": "expired"})
        result = self.cards.materialize(updated, card_id=alert_id, generated_at=self.clock(), stale_after=current.stale_after, provenance=current.provenance)
        return result

    def expire_due(self, *, now: datetime | None = None) -> tuple[str, ...]:
        checked = now or self.clock()
        due = tuple(alert_id for alert_id, (_, expires_at) in self._alerts.items() if checked >= expires_at)
        for alert_id in due:
            investigation_id, _ = self._alerts[alert_id]
            current = self.cards.get_current(alert_id)
            if current and current.status == CardStatus.ACTIVE:
                payload = current.payload
                if isinstance(payload, ProactiveAlertCard):
                    self.cards.materialize(payload.model_copy(update={"status": "expired"}), card_id=alert_id, generated_at=checked, stale_after=current.stale_after, provenance=current.provenance)
        return due

    def _required(self, alert_id: str) -> tuple[str, datetime]:
        if alert_id not in self._alerts:
            raise KeyError(alert_id)
        return self._alerts[alert_id]

    @staticmethod
    def _authorize(investigation_id: str, authorization: AuthorizationContext) -> None:
        if authorization.investigation_id != investigation_id or not ({"investigation:read", "investigation:write"} & set(authorization.scopes)):
            raise PermissionError("alert access is outside the authorized investigation scope")


__all__ = ["ProactiveAlertService"]
