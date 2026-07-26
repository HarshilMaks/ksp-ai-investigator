"""Minimal portable Runner protocol for the investigation agent boundary."""

from __future__ import annotations

from typing import Protocol

from src.domain.investigation_state import InvestigationState


class Runner(Protocol):
    """Run an agent-based investigation and return its updated state."""

    async def run(self, state: InvestigationState) -> InvestigationState:
        ...


__all__ = ["Runner"]
