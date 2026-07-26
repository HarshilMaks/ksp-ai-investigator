"""Temporary sequential Runner implementation.

This module deliberately contains no persistence, scheduling, retries, streams,
parallel execution, workflow graph, or provider/database integration. Agents
own business behavior; LocalRunner only supplies their shared context and
passes each returned InvestigationState to the next agent.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from src.domain.investigation_state import InvestigationState

from .runner import Runner
from .state import AgentContext


class LocalRunner:
    """Invoke injected agents sequentially with one shared state boundary."""

    def __init__(
        self,
        agents: Iterable[Any],
        *,
        auth_context: dict[str, object] | None = None,
        registry: object = None,
        llm: object = None,
        logger: object = None,
    ) -> None:
        self._agents: tuple[Any, ...] = tuple(agents)
        self._auth_context = dict(auth_context or {})
        self._registry = registry
        self._llm = llm
        self._logger = logger

    @property
    def agents(self) -> tuple[Any, ...]:
        """Expose the fixed invocation order for diagnostics and tests."""

        return self._agents

    async def run(self, state: InvestigationState) -> InvestigationState:
        if not isinstance(state, InvestigationState):
            raise TypeError("LocalRunner.run requires an InvestigationState")
        current = state
        for agent in self._agents:
            run = getattr(agent, "run", None)
            if not callable(run):
                raise TypeError("Every LocalRunner agent must expose async run(context)")
            result = await run(
                AgentContext(
                    state=current,
                    auth_context=self._auth_context,
                    registry=self._registry,
                    llm=self._llm,
                    logger=self._logger,
                )
            )
            if not isinstance(result, InvestigationState):
                raise TypeError("Every LocalRunner agent must return an InvestigationState")
            current = result
        return current


__all__ = ["LocalRunner"]
