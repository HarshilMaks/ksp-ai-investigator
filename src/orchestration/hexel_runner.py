"""Future Hexel adapter boundary; no Hexel dependency is implemented here."""

from __future__ import annotations

from typing import Protocol

from src.domain.investigation_state import InvestigationState

from .runner import Runner


class RunnerUnavailableError(RuntimeError):
    """The configured production runtime is not available in this environment."""


class HexelExecutionAdapter(Protocol):
    async def run(self, state: InvestigationState) -> InvestigationState:
        ...


class HexelRunner:
    """Structural adapter for a future Hexel execution boundary.

    The adapter delegates only the same Runner contract. It does not import an
    SDK, recreate fleet behavior, or silently fall back to LocalRunner.
    """

    def __init__(self, adapter: HexelExecutionAdapter | None = None) -> None:
        self._adapter = adapter

    async def run(self, state: InvestigationState) -> InvestigationState:
        if self._adapter is None:
            raise RunnerUnavailableError("Hexel runtime adapter is not configured")
        result = await self._adapter.run(state)
        if not isinstance(result, InvestigationState):
            raise TypeError("Hexel adapter must return an InvestigationState")
        return result


__all__ = ["HexelExecutionAdapter", "HexelRunner", "RunnerUnavailableError"]
