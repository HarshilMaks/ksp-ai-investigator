from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from main import build_api_application
from src.adapters.catalyst import (
    CatalystRepositorySet,
    CatalystTableRepository,
    LocalDataStore,
    LOGICAL_CATALYST_TABLES,
)
from src.adapters.card_store import CatalystCardStore
from src.domain.cards import CardProvenance, CardRecord, OffenderProfileCard
from src.domain.enums import TimelineEventType
from src.registry.tools import AuthorizationContext
from src.services.checkpoints import CatalystCheckpointStore, LocalCheckpointStore
from src.services.investigations import InvestigationService
from src.shared.config import load_settings


class CatalystRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_repository_set_uses_every_locked_logical_table(self) -> None:
        repositories = CatalystRepositorySet.from_data_store(LocalDataStore())
        self.assertEqual(
            LOGICAL_CATALYST_TABLES,
            tuple(getattr(repositories, name).table_name for name in LOGICAL_CATALYST_TABLES),
        )

    async def test_generic_crud_uses_the_declared_resource_and_key(self) -> None:
        data_store = LocalDataStore()
        repository = CatalystTableRepository(data_store)
        repository.table_name = "firs"
        repository.key_field = "fir_id"

        created = await repository.create({"fir_id": "FIR-1", "status": "OPEN"})
        self.assertEqual(created, {"fir_id": "FIR-1", "status": "OPEN"})
        self.assertEqual(await repository.get("FIR-1"), created)
        updated = await repository.update("FIR-1", {"fir_id": "FIR-1", "status": "CLOSED"})
        self.assertEqual(updated["status"], "CLOSED")
        self.assertEqual(await repository.list({"status": "CLOSED"}), (updated,))
        await repository.delete("FIR-1")
        self.assertIsNone(await repository.get("FIR-1"))

    async def test_catalyst_checkpoint_also_projects_investigation_evidence_timeline_and_audit(self) -> None:
        data_store = LocalDataStore()
        service = InvestigationService(CatalystCheckpointStore(data_store))
        owner_id = uuid4()
        authorization = AuthorizationContext(
            officer_id=str(owner_id),
            role="IO",
            scopes=frozenset({"investigation:read", "investigation:write"}),
        )
        state = await service.create(title="Normalized Catalyst state", owner_id=owner_id, authorization=authorization)
        self.assertEqual((await data_store.query("investigations", {}))[0]["status"], "OPEN")
        self.assertEqual((await data_store.query("audit_logs", {}))[0]["user_role"], "IO")

        fir_id = uuid4()
        state = await service.pin_evidence(
            state.investigation_id,
            fir_id=fir_id,
            authorization=authorization,
            request_id="evidence-1",
        )
        state = await service.add_timeline_event(
            state.investigation_id,
            event_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            event_type=TimelineEventType.WITNESS_STATEMENT,
            description="Synthetic timeline event",
            source_fir_id=fir_id,
            authorization=authorization,
        )
        evidence = await data_store.query("investigation_evidence", {"investigation_id": str(state.investigation_id)})
        timeline = await data_store.query("investigation_timeline", {"investigation_id": str(state.investigation_id)})
        audits = await data_store.query("audit_logs", {})
        self.assertEqual(len(evidence), 1)
        self.assertEqual(len(timeline), 1)
        self.assertEqual(len(audits), state.version)
        self.assertEqual(audits[-1]["action"], "UPDATE")

    async def test_intelligence_card_repository_round_trips_active_card_envelope(self) -> None:
        data_store = LocalDataStore()
        repositories = CatalystRepositorySet.from_data_store(data_store)
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        card = CardRecord(
            generated_at=now,
            stale_after=now + timedelta(days=1),
            payload=OffenderProfileCard(
                entity_id="entity-1",
                risk_level="medium",
                predicted_behavior="review",
                confidence_score=0.8,
            ),
            provenance=CardProvenance(
                engine="test-engine",
                algorithm_version="1",
                source_ids=("source-1",),
                data_snapshot="snapshot-1",
            ),
        )
        await repositories.intelligence_cards.save_card(card)
        restored = await repositories.intelligence_cards.get_card(card.card_id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.model_dump(mode="json"), card.model_dump(mode="json"))

    async def test_existing_card_service_can_use_catalyst_card_store(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        store = CatalystCardStore(LocalDataStore())
        from src.services.cards import CardService

        service = CardService(store, clock=lambda: now)
        card = service.materialize(
            OffenderProfileCard(
                entity_id="entity-2",
                risk_level="low",
                predicted_behavior="review",
                confidence_score=0.7,
            ),
            provenance=CardProvenance(
                engine="test-engine",
                algorithm_version="1",
                source_ids=("source-2",),
                data_snapshot="snapshot-2",
            ),
            stale_after=now + timedelta(days=1),
        )
        self.assertEqual(service.get_current(card.card_id).card_id, card.card_id)
        self.assertEqual(tuple(item.version for item in service.historical_versions(card.card_id)), (1,))


class CatalystCompositionTests(unittest.TestCase):
    def test_app_env_catalyst_selects_catalyst_checkpoint_store(self) -> None:
        settings = load_settings(
            {
                "APP_ENV": "catalyst",
                "CATALYST_PROJECT_ID": "synthetic-project",
                "CATALYST_APP_ID": "synthetic-app",
                "NEO4J_USER": "synthetic-user",
                "NEO4J_PASSWORD": "synthetic-password",
            }
        )
        application = build_api_application(settings=settings)
        self.assertIsInstance(application.investigations.checkpoints, CatalystCheckpointStore)

    def test_local_app_env_preserves_local_checkpoint_store(self) -> None:
        settings = load_settings({"APP_ENV": "local"})
        application = build_api_application(settings=settings)
        self.assertIsInstance(application.investigations.checkpoints, LocalCheckpointStore)


if __name__ == "__main__":
    unittest.main()
