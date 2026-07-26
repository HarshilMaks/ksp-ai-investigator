from __future__ import annotations

import asyncio
import unittest

from pydantic import ValidationError

from src.registry import (
    EXPECTED_TOOL_IDS,
    TOOL_SPECS,
    AuthorizationContext,
    RegistryError,
    ToolDispatcher,
    validate_manifest,
)
from src.registry.schemas import (
    FinancialTrailParams,
    SQLQueryParams,
    ToolCall,
    TranslateParams,
)


READ_AUTH = AuthorizationContext(
    officer_id="synthetic-officer-001",
    role="IO",
    scopes=frozenset({"ontology:read"}),
)
WRITE_AUTH = AuthorizationContext(
    officer_id="synthetic-officer-001",
    role="IO",
    scopes=frozenset({"ontology:read", "investigation:write"}),
)


class RegistryManifestTests(unittest.TestCase):
    def test_exactly_t01_to_t23_are_registered(self) -> None:
        validate_manifest()
        self.assertEqual(set(TOOL_SPECS), set(EXPECTED_TOOL_IDS))
        self.assertEqual(len(TOOL_SPECS), 23)
        self.assertTrue(all(spec.input_model and spec.output_model for spec in TOOL_SPECS.values()))
        self.assertTrue(all(spec.citation_required for spec in TOOL_SPECS.values()))
        self.assertFalse(any(spec.public_route for spec in TOOL_SPECS.values()))

    def test_locked_ownership_is_preserved_for_sensitive_tools(self) -> None:
        self.assertEqual(TOOL_SPECS["T15"].owner, "lead_ranking")
        self.assertEqual(TOOL_SPECS["T15"].stage, "deterministic")
        self.assertEqual(TOOL_SPECS["T20"].owner, "evidence_explainability")
        self.assertEqual(TOOL_SPECS["T22"].owner, "investigation_state")
        self.assertEqual(TOOL_SPECS["T22"].audit_action.value, "ADD_EVIDENCE")


class RegistrySchemaTests(unittest.TestCase):
    def test_extra_fields_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SQLQueryParams(table="firs", filters={}, unexpected="not-allowed")

    def test_cross_field_subjects_are_required(self) -> None:
        with self.assertRaises(ValidationError):
            FinancialTrailParams()
        with self.assertRaises(ValidationError):
            TranslateParams(text="hello", source_lang="en", target_lang="en")

    def test_limits_and_allowed_values_are_enforced(self) -> None:
        with self.assertRaises(ValidationError):
            ToolCall(tool_id="T03", tool_name="graph_traverse", parameters={}, timeout_ms=300_001)
        with self.assertRaises(ValidationError):
            ToolCall(tool_id="T99", tool_name="unknown", parameters={})


class RegistryDispatchTests(unittest.TestCase):
    def test_injected_handler_receives_typed_parameters_and_returns_typed_output(self) -> None:
        seen: list[object] = []

        async def handler(parameters: object, authorization: AuthorizationContext) -> dict:
            seen.append(parameters)
            self.assertEqual(authorization.role, "IO")
            self.assertIsInstance(parameters, SQLQueryParams)
            return {
                "tool_id": "T01",
                "status": "ok",
                "data": [{"fir_id": "synthetic-fir-001"}],
                "total": 1,
                "citations": [{"source_type": "FIR", "source_id": "synthetic-fir-001"}],
            }

        dispatcher = ToolDispatcher()
        dispatcher.register("T01", handler)
        output = asyncio.run(
            dispatcher.dispatch(
                {
                    "tool_id": "T01",
                    "tool_name": "sql_query",
                    "parameters": {"table": "firs", "filters": {"district": "Synthetic"}},
                },
                authorization=READ_AUTH,
            )
        )
        self.assertEqual(output.tool_id, "T01")
        self.assertEqual(output.total, 1)
        self.assertEqual(len(seen), 1)
        self.assertEqual(dispatcher.records[0].owner, "sql_retrieval")

    def test_unknown_tool_is_rejected(self) -> None:
        dispatcher = ToolDispatcher()
        with self.assertRaisesRegex(RegistryError, "not registered"):
            asyncio.run(
                dispatcher.dispatch(
                    {"tool_id": "T99", "tool_name": "unknown", "parameters": {}},
                    authorization=READ_AUTH,
                )
            )

    def test_unauthorized_and_public_routes_are_rejected(self) -> None:
        dispatcher = ToolDispatcher()
        dispatcher.register("T22", lambda parameters, auth: {"tool_id": "T22"})
        with self.assertRaisesRegex(RegistryError, "Authorization"):
            asyncio.run(
                dispatcher.dispatch(
                    {
                        "tool_id": "T22",
                        "tool_name": "pin_evidence",
                        "parameters": {
                            "investigation_id": "inv-1",
                            "evidence_type": "fir",
                            "evidence_id": "fir-1",
                        },
                    },
                    authorization=READ_AUTH,
                )
            )
        with self.assertRaisesRegex(RegistryError, "public route"):
            asyncio.run(
                dispatcher.dispatch(
                    {
                        "tool_id": "T01",
                        "tool_name": "sql_query",
                        "parameters": {"table": "firs"},
                    },
                    authorization=READ_AUTH,
                    public_route=True,
                )
            )

    def test_over_budget_request_and_missing_handler_are_rejected(self) -> None:
        dispatcher = ToolDispatcher()
        with self.assertRaisesRegex(RegistryError, "timeout"):
            asyncio.run(
                dispatcher.dispatch(
                    {
                        "tool_id": "T01",
                        "tool_name": "sql_query",
                        "timeout_ms": 30_001,
                        "parameters": {"table": "firs"},
                    },
                    authorization=READ_AUTH,
                )
            )
        with self.assertRaisesRegex(RegistryError, "handler"):
            asyncio.run(
                dispatcher.dispatch(
                    {
                        "tool_id": "T01",
                        "tool_name": "sql_query",
                        "parameters": {"table": "firs"},
                    },
                    authorization=READ_AUTH,
                )
            )


if __name__ == "__main__":
    unittest.main()
