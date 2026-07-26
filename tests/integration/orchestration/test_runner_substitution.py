from __future__ import annotations

import asyncio
import unittest
from uuid import uuid4

from src.domain.investigation_state import InvestigationState
from src.orchestration.hexel_runner import HexelRunner, RunnerUnavailableError
from src.orchestration.runner import Runner


class FakeHexelAdapter:
    async def run(self, state: InvestigationState) -> InvestigationState:
        return state.with_version(state.version + 10)


def make_state() -> InvestigationState:
    return InvestigationState(investigation_id=uuid4(), title="Runner substitution", owner_id=uuid4())


class RunnerSubstitutionTests(unittest.TestCase):
    def test_hexel_adapter_has_the_same_runner_shape_without_an_sdk(self) -> None:
        runner: Runner = HexelRunner(FakeHexelAdapter())
        result = asyncio.run(runner.run(make_state()))
        self.assertEqual(11, result.version)

    def test_missing_hexel_runtime_fails_explicitly(self) -> None:
        with self.assertRaises(RunnerUnavailableError):
            asyncio.run(HexelRunner().run(make_state()))


if __name__ == "__main__":
    unittest.main()
