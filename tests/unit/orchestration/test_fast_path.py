from __future__ import annotations

import asyncio
import unittest

from src.engines.evidence import EvidenceGate
from src.orchestration.fast_path import FastPathError, FastPathExecutor
from src.orchestration.router import FastPathRouter
from src.registry import AuthorizationContext, ToolDispatcher
from src.registry.manifest import get_tool_spec
from src.registry.schemas import AnalysisOutput, RetrievalOutput


AUTH = AuthorizationContext(
    officer_id="synthetic-officer-001",
    role="IO",
    scopes=frozenset({"ontology:read"}),
)


class FastPathRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = FastPathRouter()

    def test_structured_deterministic_tools_use_fast_path(self) -> None:
        decision = self.router.classify(
            {"tool_id": "T01", "tool_name": "sql_query", "parameters": {"table": "firs"}}
        )
        self.assertEqual(decision.route, "fast")
        self.assertEqual(decision.tool_id, "T01")

    def test_reasoning_or_natural_language_does_not_use_fast_path(self) -> None:
        decision = self.router.classify(
            {"tool_id": "T20", "tool_name": "explain_reasoning", "parameters": {
                "conclusion": "test", "evidence_chain": ["fir-1"], "confidence": 0.5,
            }}
        )
        self.assertEqual(decision.route, "deep")
        self.assertEqual(self.router.classify_text("Who is connected to this FIR?").route, "deep")


class FastPathExecutionTests(unittest.TestCase):
    def test_successful_result_is_released_with_citations_and_audit(self) -> None:
        async def handler(parameters: object, authorization: AuthorizationContext) -> dict:
            return {
                "tool_id": "T01",
                "status": "ok",
                "data": [{"fir_id": "fir-1", "crime_category": "Cybercrime"}],
                "total": 1,
                "citations": [{"source_type": "FIR", "source_id": "fir-1"}],
            }

        dispatcher = ToolDispatcher()
        dispatcher.register("T01", handler)
        executor = FastPathExecutor(dispatcher)
        response = asyncio.run(
            executor.execute(
                {"tool_id": "T01", "tool_name": "sql_query", "parameters": {"table": "firs"}},
                authorization=AUTH,
                request_id="request-1",
            )
        )
        self.assertTrue(response.released)
        self.assertEqual(response.tool_id, "T01")
        self.assertEqual(response.citations[0]["source_id"], "fir-1")
        self.assertEqual(response.audit["request_id"], "request-1")
        self.assertEqual(response.uncertainty["type"], "deterministic_engine")

    def test_missing_citations_are_blocked(self) -> None:
        dispatcher = ToolDispatcher()
        dispatcher.register(
            "T01",
            lambda parameters, authorization: {
                "tool_id": "T01",
                "status": "ok",
                "data": [{"fir_id": "fir-1"}],
                "total": 1,
            },
        )
        response = asyncio.run(
            FastPathExecutor(dispatcher).execute(
                {"tool_id": "T01", "tool_name": "sql_query", "parameters": {"table": "firs"}},
                authorization=AUTH,
            )
        )
        self.assertFalse(response.released)
        self.assertIn("no citations", " ".join(response.errors))

    def test_inconsistent_total_is_blocked(self) -> None:
        dispatcher = ToolDispatcher()
        dispatcher.register(
            "T01",
            lambda parameters, authorization: {
                "tool_id": "T01",
                "status": "ok",
                "data": [{"fir_id": "fir-1"}],
                "total": 0,
                "citations": [{"source_type": "FIR", "source_id": "fir-1"}],
            },
        )
        response = asyncio.run(
            FastPathExecutor(dispatcher).execute(
                {"tool_id": "T01", "tool_name": "sql_query", "parameters": {"table": "firs"}},
                authorization=AUTH,
            )
        )
        self.assertFalse(response.released)
        self.assertIn("total", " ".join(response.errors))

    def test_deep_path_call_is_rejected_before_handler_execution(self) -> None:
        dispatcher = ToolDispatcher()
        dispatcher.register("T20", lambda parameters, authorization: {"tool_id": "T20"})
        with self.assertRaises(FastPathError):
            asyncio.run(
                FastPathExecutor(dispatcher).execute(
                    {"tool_id": "T20", "tool_name": "explain_reasoning", "parameters": {
                        "conclusion": "test", "evidence_chain": ["fir-1"], "confidence": 0.5,
                    }},
                    authorization=AUTH,
                )
            )


class EvidenceGateTests(unittest.TestCase):
    def test_contradictions_are_surfaced_and_block_release(self) -> None:
        output = AnalysisOutput(
            tool_id="T08",
            status="partial",
            data={"contradictions": [{"source_id": "fir-1", "source_id_2": "fir-2"}]},
            citations=[{"source_type": "FIR", "source_id": "fir-1"}],
        )
        decision = EvidenceGate().validate(
            output,
            spec=get_tool_spec("T08"),
            authorization=AUTH,
            request_id="request-2",
        )
        self.assertFalse(decision.released)
        self.assertIn("contradiction", " ".join(decision.warnings))
        self.assertIn("contradiction", " ".join(decision.errors))


if __name__ == "__main__":
    unittest.main()
