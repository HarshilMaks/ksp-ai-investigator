from __future__ import annotations

import asyncio
import unittest
from uuid import uuid4

from src.agents.intelligence import GraphIntelligenceAgent, interpret_validated_result
from src.domain.investigation_state import InvestigationState
from src.engines.graph_intelligence import GraphEdge, GraphNode, analyze_graph
from src.orchestration.state import AgentContext


class AgentCapabilityTests(unittest.TestCase):
    def test_agent_interprets_engine_provenance_without_recomputing(self) -> None:
        result = analyze_graph(
            [GraphNode("a", frozenset({"Person"}), {}), GraphNode("b", frozenset({"Person"}), {})],
            [GraphEdge("e", "a", "b", "KNOWS", {"evidence_fir_ids": ["fir-1"]})],
        )
        finding = interpret_validated_result(result, capability="graph_intelligence")
        self.assertEqual(("fir-1",), finding.source_ids)
        state = InvestigationState(investigation_id=uuid4(), title="Synthetic capability", owner_id=uuid4())
        agent = GraphIntelligenceAgent(result)
        returned = asyncio.run(agent.run(AgentContext(state, {}, None, None, None)))
        self.assertIs(state, returned)
        self.assertEqual(finding, agent.last_finding)

    def test_unbounded_or_unvalidated_result_is_rejected(self) -> None:
        class Invalid:
            metadata = type("Metadata", (), {"bounded": False, "algorithm": "bad"})()
            uncertainty = type("Uncertainty", (), {"kind": "unknown", "confidence": 0.0})()

        with self.assertRaises(TypeError):
            interpret_validated_result(Invalid(), capability="graph_intelligence")


if __name__ == "__main__":
    unittest.main()
