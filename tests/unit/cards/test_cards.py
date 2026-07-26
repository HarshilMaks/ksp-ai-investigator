from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from src.adapters.card_store import InMemoryCardStore, LocalCardStore
from src.domain.cards import (
    ALL_CARD_TYPES, CaseSummaryCard, CardProvenance, CardStatus, CardType, CriminalNetworkCard,
    CrimeHotspotCard, EntityResolutionCard, EvidenceSummaryCard, FinancialTrailCard, ForecastCard,
    HypothesisCard, InvestigationTimelineCard, LeadCard, OffenderProfileCard, ProactiveAlertCard,
    ReasoningTraceCard, SimilarCaseCard, SociologicalInsightCard,
)
from src.services.cards import CardService

NOW = datetime(2025, 1, 1, tzinfo=timezone.utc)
PROVENANCE = CardProvenance(engine="test-engine", algorithm_version="test-1", source_ids=("source-1",), data_snapshot="snapshot-1")


def payloads() -> list[object]:
    return [
        OffenderProfileCard(entity_id="e", risk_level="medium", predicted_behavior="review", confidence_score=.5),
        CriminalNetworkCard(network_id="n", members=(), total_edges=0, density=0, confidence_score=.5),
        FinancialTrailCard(trail_id="t", source_account="a", destination_account="b", hops=(), total_amount=0, confidence_score=.5),
        CrimeHotspotCard(hexagon_id="h", district="d", crime_category="fraud", trend_direction="stable", forecast_confidence=.5, confidence_score=.5),
        SimilarCaseCard(source_fir_id="a", matched_fir_id="b", overall_similarity=.5, similarity_dimensions={}, confidence_score=.5),
        InvestigationTimelineCard(investigation_id="i", events=(), total_events=0, completeness_score=.5),
        HypothesisCard(hypothesis_id="h", investigation_id="i", statement="test", status="active", confidence_score=.5),
        EvidenceSummaryCard(investigation_id="i", total_evidence_items=0, categories={}, overall_evidence_strength=.5, chain_of_custody_status="partial"),
        LeadCard(lead_id="l", investigation_id="i", action="review", rationale="source", priority="medium", confidence=.5, status="pending"),
        EntityResolutionCard(resolution_id="r", entity_a_id="a", entity_b_id="b", overall_confidence=.5, recommended_action="officer_review"),
        ProactiveAlertCard(alert_id="a", investigation_id="i", what_changed="new", why_it_matters="review", confidence=.5, urgency="routine", status="new"),
        SociologicalInsightCard(insight_id="s", area={}, crime_type="fraud", correlation_factors=(), qualification="Correlation does not imply causation.", confidence_score=.5),
        ForecastCard(forecast_id="f", district="d", crime_category="fraud", forecasts=(), confidence_score=.5),
        CaseSummaryCard(investigation_id="i", summary_version=1, key_facts=(), narrative="summary", investigation_progress=.5),
        ReasoningTraceCard(trace_id="r", parent_card_id="p", parent_card_type="lead", question="why", chain=(), conclusion="review", conclusion_confidence=.5),
    ]


class CardLifecycleTests(unittest.TestCase):
    def test_all_locked_card_types_have_typed_payloads(self) -> None:
        values = payloads()
        self.assertEqual(15, len(ALL_CARD_TYPES))
        self.assertEqual(set(ALL_CARD_TYPES), {payload.card_type for payload in values})
        self.assertTrue(all(payload.requires_human_review for payload in values))

    def test_materialization_is_versioned_and_historical(self) -> None:
        store = InMemoryCardStore()
        service = CardService(store, clock=lambda: NOW)
        first = service.materialize(payloads()[8], provenance=PROVENANCE, stale_after=NOW + timedelta(days=1))
        second = service.materialize(payloads()[8], provenance=PROVENANCE, stale_after=NOW + timedelta(days=1), card_id=first.card_id)
        self.assertEqual((1, 2), tuple(card.version for card in service.historical_versions(first.card_id)))
        self.assertEqual(2, second.version)
        self.assertEqual(first.card_id, second.supersedes_card_id)

    def test_stale_and_archive_transitions_are_explicit(self) -> None:
        store = InMemoryCardStore()
        service = CardService(store, clock=lambda: NOW)
        card = service.materialize(payloads()[8], provenance=PROVENANCE, stale_after=NOW + timedelta(days=1))
        self.assertEqual(CardStatus.STALE, service.get_current(card.card_id, at=NOW + timedelta(days=2)).status)
        archived = service.archive(card.card_id)
        self.assertEqual(CardStatus.ARCHIVED, archived.status)
        self.assertEqual(2, archived.version)

    def test_local_canonical_json_survives_new_store_instance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first_store = LocalCardStore(directory)
            card = CardService(first_store, clock=lambda: NOW).materialize(payloads()[0], provenance=PROVENANCE, stale_after=NOW + timedelta(days=1))
            second_store = LocalCardStore(directory)
            restored = second_store.get(card.card_id)
            self.assertIsNotNone(restored)
            self.assertEqual(card.model_dump(mode="json"), restored.model_dump(mode="json"))
            self.assertTrue((__import__("pathlib").Path(directory) / "metadata-index.json").exists())


if __name__ == "__main__":
    unittest.main()
