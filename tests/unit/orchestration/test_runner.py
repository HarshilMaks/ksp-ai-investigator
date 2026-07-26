from __future__ import annotations

import asyncio
import unittest
from uuid import uuid4

from src.domain.investigation_state import InvestigationState
from src.orchestration.local_runner import LocalRunner
from src.orchestration.state import AgentContext


class RecordingAgent:
    def __init__(self, name: str, calls: list[tuple[str, int]]) -> None:
        self.name = name
        self.calls = calls

    async def run(self, context: AgentContext) -> InvestigationState:
        self.calls.append((self.name, context.state.version))
        return context.state.with_version(context.state.version + 1)


class InvalidAgent:
    async def run(self, context: AgentContext) -> object:
        return {"not": "state"}


def make_state() -> InvestigationState:
    officer_id = uuid4()
    return InvestigationState(investigation_id=uuid4(), title="Synthetic runner test", owner_id=officer_id)


class LocalRunnerTests(unittest.TestCase):
    def test_agents_receive_updated_state_in_declared_order(self) -> None:
        calls: list[tuple[str, int]] = []
        runner = LocalRunner(
            [RecordingAgent("planner", calls), RecordingAgent("evidence", calls), RecordingAgent("reporter", calls)],
            auth_context={"officer_id": "officer-1"},
            registry=object(),
            llm=object(),
            logger=object(),
        )
        result = asyncio.run(runner.run(make_state()))
        self.assertEqual(["planner", "evidence", "reporter"], [name for name, _ in calls])
        self.assertEqual([1, 2, 3], [version for _, version in calls])
        self.assertEqual(4, result.version)

    def test_runner_rejects_invalid_agent_result(self) -> None:
        with self.assertRaises(TypeError):
            asyncio.run(LocalRunner([InvalidAgent()]).run(make_state()))

    def test_context_is_one_state_boundary_and_auth_is_not_shared_mutably(self) -> None:
        context = AgentContext(state=make_state(), auth_context={"role": "IO"}, registry=None, llm=None, logger=None)
        self.assertIsInstance(context.state, InvestigationState)
        self.assertEqual({"role": "IO"}, context.auth_context)
        with self.assertRaises(Exception):
            context.state = make_state()  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
