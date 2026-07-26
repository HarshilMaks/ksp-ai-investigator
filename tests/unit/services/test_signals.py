from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from src.adapters.card_store import InMemoryCardStore
from src.registry.tools import AuthorizationContext
from src.services.entity_resolution import EntityResolutionService, ResolutionStatus
from src.services.proactive_alerts import ProactiveAlertService
from src.services.signals import FIRSignal, SignalIngestionService

NOW = datetime(2025, 1, 1, tzinfo=timezone.utc)
AUTH = AuthorizationContext("officer-1", "IO", frozenset({"investigation:write"}), investigation_id="inv-1")


class P15SignalTests(unittest.TestCase):
    def test_fir_replay_is_idempotent_and_matches_only_watched_investigations(self) -> None:
        callbacks: list[str] = []
        service = SignalIngestionService(on_new_fir=lambda signal: callbacks.append(signal.fir_id))
        signal = FIRSignal("event-1", "fir-1", ("entity-1", "entity-2"), "linked activity", ("fir-1",), NOW)
        first = service.ingest(signal, active_investigations=(("inv-1", frozenset({"entity-1"})), ("inv-2", frozenset({"other"}))))
        replay = service.ingest(signal, active_investigations=(("inv-1", frozenset({"entity-1"})),))
        self.assertFalse(first.duplicate)
        self.assertEqual(("inv-1",), tuple(match.investigation_id for match in first.matches))
        self.assertTrue(replay.duplicate)
        self.assertEqual(["fir-1"], callbacks)
        self.assertEqual(1, len(service.signals))

    def test_person_resolution_requires_explicit_approval_but_locked_identifier_can_auto_merge(self) -> None:
        service = EntityResolutionService()
        person = service.resolve(resolution_id="r-person", entity_type="person", entity_a_id="a", entity_b_id="b", identifiers_a={"phone": "999"}, identifiers_b={"phone": "999"})
        self.assertEqual(ResolutionStatus.SUGGESTED, person.status)
        self.assertFalse(service.is_merged("a", "b"))
        approved = service.approve("r-person", officer_id="officer-1")
        self.assertEqual(ResolutionStatus.APPROVED, approved.status)
        self.assertTrue(service.is_merged("a", "b"))
        vehicle = service.resolve(resolution_id="r-vehicle", entity_type="vehicle", entity_a_id="v1", entity_b_id="v2", identifiers_a={"vehicle_registration": "KA 01 AB 1234"}, identifiers_b={"vehicle_registration": "ka-01-ab-1234"})
        self.assertEqual(ResolutionStatus.AUTO_MERGED, vehicle.status)

    def test_proactive_alert_is_scoped_acknowledgeable_and_expires(self) -> None:
        service = ProactiveAlertService(InMemoryCardStore(), clock=lambda: NOW, ttl=timedelta(hours=48))
        signal = FIRSignal("event-2", "fir-2", ("entity-1",), "review new linked FIR", ("fir-2",), NOW)
        alert = service.create_for_match(signal, investigation_id="inv-1", authorization=AUTH)
        self.assertEqual("new", alert.payload.status)
        acknowledged = service.acknowledge(alert.payload.alert_id, officer_id="officer-1", authorization=AUTH)
        self.assertEqual("acknowledged", acknowledged.payload.status)
        with self.assertRaises(PermissionError):
            service.create_for_match(signal, investigation_id="inv-2", authorization=AUTH)
        expired = service.expire_due(now=NOW + timedelta(hours=49))
        self.assertEqual((alert.payload.alert_id,), expired)


if __name__ == "__main__":
    unittest.main()
