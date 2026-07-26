"""Reusable agent contracts and temporary no-op Strands-compatible seams.

P12 defines the invocation boundary only. Deterministic business capabilities
are connected to these agents in P13; these classes never call another agent,
write persistence, or access infrastructure directly.
"""

from __future__ import annotations

from typing import Protocol

from src.domain.investigation_state import InvestigationState
from src.orchestration.state import AgentContext


class AgentProtocol(Protocol):
    async def run(self, context: AgentContext) -> InvestigationState:
        ...


class StateAgent:
    """Small Strands-compatible state agent seam for dependency injection."""

    name = "state-agent"

    async def run(self, context: AgentContext) -> InvestigationState:
        if not isinstance(context, AgentContext):
            raise TypeError("agent run requires AgentContext")
        return context.state


class Planner(StateAgent):
    name = "planner"


class Evidence(StateAgent):
    name = "evidence"


class GraphIntelligence(StateAgent):
    name = "graph-intelligence"


class PatternIntelligence(StateAgent):
    name = "pattern-intelligence"


class FinancialIntelligence(StateAgent):
    name = "financial-intelligence"


class Timeline(StateAgent):
    name = "timeline"


class Reasoner(StateAgent):
    name = "reasoner"


class Reporter(StateAgent):
    name = "reporter"


DEFAULT_AGENT_SEQUENCE: tuple[type[StateAgent], ...] = (
    Planner,
    Evidence,
    GraphIntelligence,
    PatternIntelligence,
    FinancialIntelligence,
    Timeline,
    Reasoner,
    Reporter,
)

PlannerAgent = Planner
EvidenceAgent = Evidence
GraphIntelligenceAgent = GraphIntelligence
PatternIntelligenceAgent = PatternIntelligence
FinancialIntelligenceAgent = FinancialIntelligence
TimelineAgent = Timeline
ReasonerAgent = Reasoner
ReporterAgent = Reporter

__all__ = [
    "AgentProtocol",
    "StateAgent",
    "Planner",
    "Evidence",
    "GraphIntelligence",
    "PatternIntelligence",
    "FinancialIntelligence",
    "Timeline",
    "Reasoner",
    "Reporter",
    "DEFAULT_AGENT_SEQUENCE",
]
