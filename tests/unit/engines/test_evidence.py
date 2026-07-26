from __future__ import annotations

import unittest

from src.engines.evidence import EvidenceGate
from src.registry import AuthorizationContext
from src.registry.manifest import get_tool_spec
from src.registry.schemas import RetrievalOutput


class EvidenceEngineTests(unittest.TestCase):
    def test_citation_coverage_and_source_metadata_are_released(self) -> None:
        output = RetrievalOutput(
            tool_id="T01",
            data=[{"fir_id": "fir-1"}],
            total=1,
            citations=[{"source_type": "FIR", "source_id": "fir-1"}],
        )
        decision = EvidenceGate().validate(
            output,
            spec=get_tool_spec("T01"),
            authorization=AuthorizationContext(
                officer_id="officer-1",
                role="IO",
                scopes=frozenset({"ontology:read"}),
            ),
        )
        self.assertTrue(decision.released)
        self.assertEqual(decision.source_coverage, 1.0)
        self.assertEqual(decision.claims[0].source_ids, ("fir-1",))


if __name__ == "__main__":
    unittest.main()
