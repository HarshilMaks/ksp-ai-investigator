from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone

from src.engines.behavioral_profiling import BehavioralEvent, profile_behavior
from src.engines.financial_analysis import FinancialTransaction, analyze_financial_flow
from src.engines.forecasting import ForecastObservation, forecast_hotspots
from src.engines.graph_intelligence import GraphEdge, GraphNode, analyze_graph
from src.engines.lead_ranking import LeadCandidate, rank_leads
from src.engines.pattern_analysis import PatternEvent, analyze_patterns
from src.engines.timeline import TimelineInput, reconstruct_timeline

UTC = timezone.utc


class P13EngineTests(unittest.TestCase):
    def test_graph_is_bounded_and_reproducible_with_provenance(self) -> None:
        nodes = [GraphNode("a", frozenset({"Person"}), {}), GraphNode("b", frozenset({"Person"}), {}), GraphNode("c", frozenset({"Account"}), {})]
        edges = [GraphEdge("e1", "a", "b", "KNOWS", {"evidence_fir_ids": ["fir-1"]}), GraphEdge("e2", "b", "c", "USES", {"evidence_fir_ids": ["fir-2"]})]
        first, second = analyze_graph(nodes, edges), analyze_graph(nodes, edges)
        self.assertEqual(first, second)
        self.assertTrue(first.metadata.bounded)
        self.assertEqual({"fir-1", "fir-2"}, {source.source_id for item in first.centrality for source in item.evidence})
        with self.assertRaises(ValueError):
            analyze_graph(nodes, edges, max_hops=6)

    def test_pattern_behavior_and_financial_outputs_are_cited(self) -> None:
        times = [datetime(2025, 1, 1, 8, tzinfo=UTC), datetime(2025, 1, 2, 9, tzinfo=UTC)]
        pattern = analyze_patterns([PatternEvent("p1", "subject", times[0], "ATM", source_ids=("fir-1",)), PatternEvent("p2", "subject", times[1], "ATM", source_ids=("fir-2",))])
        behavior = profile_behavior([BehavioralEvent("b1", "subject", times[0], "ATM", .4, ("fir-1",)), BehavioralEvent("b2", "subject", times[1], "ATM", .6, ("fir-2",))])
        financial = analyze_financial_flow([FinancialTransaction("t1", "a", "b", 100.0, times[0], "UPI", ("tx-1",)), FinancialTransaction("t2", "b", "a", 80.0, times[1], "UPI", ("tx-2",))])
        self.assertEqual(pattern, analyze_patterns([PatternEvent("p1", "subject", times[0], "ATM", source_ids=("fir-1",)), PatternEvent("p2", "subject", times[1], "ATM", source_ids=("fir-2",))]))
        self.assertEqual(("increasing",), tuple(item.severity_direction for item in behavior.profiles))
        self.assertTrue(financial.indicators.round_tripping)
        self.assertTrue(financial.flows[0].evidence)

    def test_forecast_timeline_and_lead_ranking_are_deterministic_and_qualified(self) -> None:
        observations = [ForecastObservation(f"o{i}", "station-a", date(2025, 1, i), i, (f"fir-{i}",)) for i in (1, 2, 3)]
        forecast = forecast_hotspots(observations)
        timeline = reconstruct_timeline([TimelineInput("e2", datetime(2025, 1, 3, tzinfo=UTC), "later", source_ids=("s2",)), TimelineInput("e1", datetime(2025, 1, 1, tzinfo=UTC), "first", source_ids=("s1",))])
        leads = rank_leads([LeadCandidate("l2", "Review account", .8, .4, .8, source_ids=("s2",)), LeadCandidate("l1", "Verify witness", .8, .8, .6, source_ids=("s1",))])
        self.assertEqual(("increasing",), tuple(signal.trend for signal in forecast.signals))
        self.assertEqual(("e1", "e2"), tuple(item.event_id for item in timeline.events))
        self.assertEqual("l1", leads.leads[0].lead_id)
        self.assertTrue(leads.uncertainty.limitations)

    def test_empty_and_partial_inputs_fail_safe_without_inventing_evidence(self) -> None:
        self.assertEqual(0.0, forecast_hotspots([]).uncertainty.confidence)
        self.assertEqual(0.0, reconstruct_timeline([]).uncertainty.confidence)
        self.assertEqual((), rank_leads([]).leads)
        self.assertEqual((), analyze_patterns([]).modus_operandi)


if __name__ == "__main__":
    unittest.main()
