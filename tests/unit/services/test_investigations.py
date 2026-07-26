from __future__ import annotations

import asyncio
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.adapters.catalyst.local import LocalDataStore
from src.domain.investigation_state import (
    InvestigationLifecycle,
    InvestigationStateError,
    HypothesisStatus,
    LeadStatus,
)
from src.domain.enums import Priority, TimelineEventType
from src.registry.tools import AuthorizationContext
from src.services.checkpoints import CatalystCheckpointStore, CheckpointConflict, LocalCheckpointStore
from src.services.investigations import InvestigationAuthorizationError, InvestigationService, InvestigationServiceError


UTC = timezone.utc


class InvestigationServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.owner_id = uuid4()
        self.auth = AuthorizationContext(
            officer_id=str(self.owner_id),
            role="IO",
            scopes=frozenset({"investigation:read", "investigation:write"}),
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    async def _create(self) -> tuple[InvestigationService, object]:
        service = InvestigationService(LocalCheckpointStore(self.root))
        state = await service.create(title="Synthetic Whitefield Investigation", owner_id=self.owner_id, authorization=self.auth)
        return service, state

    async def test_lifecycle_transitions_are_validated_and_archived_state_is_read_only(self) -> None:
        service, state = await self._create()
        self.assertEqual(state.status, InvestigationLifecycle.CREATED)
        state = await service.transition(state.investigation_id, InvestigationLifecycle.ACTIVE, authorization=self.auth)
        state = await service.transition(state.investigation_id, InvestigationLifecycle.SUSPENDED, authorization=self.auth)
        state = await service.transition(state.investigation_id, InvestigationLifecycle.ACTIVE, authorization=self.auth)
        state = await service.transition(state.investigation_id, InvestigationLifecycle.CLOSED, authorization=self.auth)
        self.assertIsNotNone(state.closed_at)
        state = await service.transition(state.investigation_id, InvestigationLifecycle.ARCHIVED, authorization=self.auth)
        self.assertEqual(state.status, InvestigationLifecycle.ARCHIVED)
        with self.assertRaises(InvestigationServiceError):
            await service.pin_evidence(state.investigation_id, fir_id=uuid4(), authorization=self.auth)
        with self.assertRaises(InvestigationServiceError):
            await service.transition(state.investigation_id, InvestigationLifecycle.ACTIVE, authorization=self.auth)

    async def test_invalid_transition_fails_closed(self) -> None:
        service, state = await self._create()
        with self.assertRaises(InvestigationServiceError) as context:
            await service.transition(state.investigation_id, InvestigationLifecycle.CLOSED, authorization=self.auth)
        self.assertEqual(context.exception.code, "INVESTIGATION_INVALID_TRANSITION")

    async def test_checkpoint_round_trip_survives_new_service_instance(self) -> None:
        service, state = await self._create()
        state = await service.transition(state.investigation_id, InvestigationLifecycle.ACTIVE, authorization=self.auth)
        second_service = InvestigationService(LocalCheckpointStore(self.root))
        restored = await second_service.get(state.investigation_id, authorization=self.auth)
        self.assertEqual(restored.version, 2)
        self.assertEqual(restored.status, InvestigationLifecycle.ACTIVE)
        self.assertEqual(restored.checkpoint_id, f"{state.investigation_id}:v2")
        self.assertEqual(await second_service.checkpoints.versions(state.investigation_id), (1, 2))

    async def test_evidence_hypothesis_timeline_lead_graph_and_health_stay_synchronized(self) -> None:
        service, state = await self._create()
        state = await service.transition(state.investigation_id, InvestigationLifecycle.ACTIVE, authorization=self.auth)
        fir_id = uuid4()
        entity_a = uuid4()
        entity_b = uuid4()
        state = await service.pin_evidence(
            state.investigation_id, fir_id=fir_id, tags=("financial", "witness"), authorization=self.auth, request_id="pin-1"
        )
        state = await service.pin_evidence(state.investigation_id, entity_id=entity_a, authorization=self.auth, request_id="pin-2")
        state = await service.pin_evidence(state.investigation_id, entity_id=entity_b, authorization=self.auth, request_id="pin-3")
        state = await service.add_note(state.investigation_id, text="Officer review note", tags=("important",), authorization=self.auth)
        state = await service.add_hypothesis(
            state.investigation_id,
            statement="The synthetic incidents may share an operator.",
            supporting_evidence_ids=(f"fir:{fir_id}",),
            contradicting_evidence_ids=("missing-cdr",),
            missing_critical_evidence=("CDR",),
            confidence=0.6,
            authorization=self.auth,
        )
        hypothesis_id = state.hypotheses[0].hypothesis_id
        state = await service.update_hypothesis(
            state.investigation_id, hypothesis_id, status=HypothesisStatus.INCONCLUSIVE, confidence=0.55, authorization=self.auth
        )
        state = await service.add_timeline_event(
            state.investigation_id,
            event_time=datetime(2026, 1, 1, tzinfo=UTC),
            event_type=TimelineEventType.WITNESS_STATEMENT,
            description="Synthetic witness statement recorded.",
            source_fir_id=fir_id,
            authorization=self.auth,
        )
        state = await service.add_lead(
            state.investigation_id,
            title="Request CDR",
            description="Request authorized call-detail records for review.",
            source_ids=(f"fir:{fir_id}",),
            priority=Priority.HIGH,
            authorization=self.auth,
        )
        lead_id = state.leads[0].lead_id
        state = await service.update_lead(state.investigation_id, lead_id, status=LeadStatus.ASSIGNED, authorization=self.auth)
        state = await service.update_graph_view(
            state.investigation_id,
            expanded_entity_ids=(entity_a, entity_b),
            selected_entity_id=entity_a,
            relationship_filters=("CALLED",),
            zoom=1.5,
            authorization=self.auth,
        )

        self.assertEqual(len(state.evidence), 3)
        self.assertEqual(len(state.notes), 1)
        self.assertEqual(len(state.hypotheses), 1)
        self.assertEqual(state.hypotheses[0].status, HypothesisStatus.INCONCLUSIVE)
        self.assertEqual(len(state.timeline), 1)
        self.assertEqual(state.leads[0].status, LeadStatus.ASSIGNED)
        self.assertEqual(state.graph_view.selected_entity_id, entity_a)
        self.assertEqual(state.health.evidence_coverage, 0.6)
        self.assertEqual(state.health.financial_coverage, 1.0)
        self.assertEqual(state.health.witness_coverage, 1.0)
        self.assertEqual(state.health.contradiction_count, 1)
        self.assertIn("CDR", state.hypotheses[0].missing_critical_evidence)
        self.assertTrue(all(item.source_ids or item.metric == "contradictions" for item in state.health.provenance))
        self.assertEqual(state.version, len(state.audit_log))
        self.assertEqual(state.audit_log[-1].previous_hash, state.audit_log[-2].record_hash)

    async def test_unauthorized_mutation_and_cross_investigation_scope_are_rejected(self) -> None:
        service, state = await self._create()
        outsider = AuthorizationContext(
            officer_id=str(uuid4()), role="IO", scopes=frozenset({"investigation:read", "investigation:write"})
        )
        with self.assertRaises(InvestigationAuthorizationError):
            await service.pin_evidence(state.investigation_id, fir_id=uuid4(), authorization=outsider)
        scoped = AuthorizationContext(
            officer_id=str(self.owner_id), role="IO", scopes=frozenset({"investigation:write"}), investigation_id=str(uuid4())
        )
        with self.assertRaises(InvestigationAuthorizationError):
            await service.pin_evidence(state.investigation_id, fir_id=uuid4(), authorization=scoped)

    async def test_local_checkpoint_detects_stale_versions(self) -> None:
        service, state = await self._create()
        store = LocalCheckpointStore(self.root)
        with self.assertRaises(CheckpointConflict):
            await store.save(state, expected_version=None)
        self.assertEqual((await store.load(state.investigation_id)).version, 1)

    async def test_catalyst_compatible_store_uses_same_serialized_contract(self) -> None:
        data_store = LocalDataStore()
        store = CatalystCheckpointStore(data_store)
        service = InvestigationService(store)
        state = await service.create(title="Catalyst-shaped state", owner_id=self.owner_id, authorization=self.auth)
        restored = await InvestigationService(CatalystCheckpointStore(data_store)).get(state.investigation_id, authorization=self.auth)
        self.assertEqual(restored.to_record(), state.to_record())


class InvestigationStateValidationTests(unittest.TestCase):
    def test_graph_zoom_and_required_lead_sources_are_validated(self) -> None:
        from src.domain.investigation_state import GraphViewState, Lead

        with self.assertRaises(InvestigationStateError):
            GraphViewState(zoom=0)
        with self.assertRaises(InvestigationStateError):
            Lead(title="No source", description="Invalid", created_by=uuid4(), source_ids=())


if __name__ == "__main__":
    unittest.main()
