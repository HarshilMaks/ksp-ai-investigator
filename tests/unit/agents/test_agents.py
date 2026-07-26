from __future__ import annotations

import asyncio
import unittest
from uuid import uuid4

from src.agents import DEFAULT_AGENT_SEQUENCE, Evidence, Planner, Reporter
from src.domain.investigation_state import InvestigationState
from src.orchestration.state import AgentContext


def make_context() -> AgentContext:
    return AgentContext(
        state=InvestigationState(investigation_id=uuid4(), title="Synthetic agent test", owner_id=uuid4()),
        auth_context={"role": "Analyst"},
        registry=object(),
        llm=object(),
        logger=object(),
    )


class AgentContractTests(unittest.TestCase):
    def test_all_required_agents_accept_context_and_return_shared_state(self) -> None:
        context = make_context()
        self.assertEqual(8, len(DEFAULT_AGENT_SEQUENCE))
        for agent_type in DEFAULT_AGENT_SEQUENCE:
            result = asyncio.run(agent_type().run(context))
            self.assertIs(result, context.state)

    def test_agents_do_not_orchestrate_other_agents(self) -> None:
        self.assertEqual("planner", Planner.name)
        self.assertEqual("evidence", Evidence.name)
        self.assertEqual("reporter", Reporter.name)
        for agent_type in DEFAULT_AGENT_SEQUENCE:
            self.assertFalse(hasattr(agent_type, "agents"))


if __name__ == "__main__":
    unittest.main()
