"""Shared dependency-injected state/context contracts for the temporary runner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from src.domain.investigation_state import InvestigationState


@dataclass(frozen=True)
class AgentContext:
    """The complete input boundary for one agent invocation.

    The context contains references to existing application boundaries only. It
    is intentionally not a memory store, persistence handle, provider client,
    or orchestration service.
    """

    state: InvestigationState
    auth_context: dict[str, object]
    registry: object
    llm: object
    logger: object

    def __post_init__(self) -> None:
        if not isinstance(self.state, InvestigationState):
            raise TypeError("AgentContext.state must be an InvestigationState")
        object.__setattr__(self, "auth_context", dict(self.auth_context))


__all__ = ["AgentContext"]
