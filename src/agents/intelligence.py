"""Small agent-side interpreters for validated P13 engine results.

These adapters deliberately do not recompute facts. They read the typed result
and expose a cited finding for an application caller while returning the shared
InvestigationState through the P12 agent contract.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any

from src.domain.investigation_state import InvestigationState
from src.engines.intelligence_types import SourceEvidence
from src.orchestration.state import AgentContext


@dataclass(frozen=True)
class AgentFinding:
    capability: str
    algorithm: str
    source_ids: tuple[str, ...]
    uncertainty_kind: str
    confidence: float
    requires_human_review: bool = True


def interpret_validated_result(result: object, *, capability: str) -> AgentFinding:
    metadata = getattr(result, "metadata", None)
    uncertainty = getattr(result, "uncertainty", None)
    if metadata is None or uncertainty is None or not getattr(metadata, "bounded", False):
        raise TypeError("agent can interpret only a bounded engine result")
    if not getattr(capability, "strip", lambda: "")():
        raise ValueError("capability is required")
    sources = tuple(sorted({source.source_id for source in _sources(result)}))
    return AgentFinding(capability, metadata.algorithm, sources, uncertainty.kind, uncertainty.confidence, True)


def _sources(value: object) -> list[SourceEvidence]:
    if isinstance(value, SourceEvidence):
        return [value]
    if is_dataclass(value):
        found: list[SourceEvidence] = []
        for field in fields(value):
            found.extend(_sources(getattr(value, field.name)))
        return found
    if isinstance(value, (tuple, list)):
        found = []
        for item in value:
            found.extend(_sources(item))
        return found
    return []


class EngineCapabilityAgent:
    """Interpret one injected, already-computed engine result."""

    def __init__(self, capability: str, result: object) -> None:
        self.capability = capability
        self.result = result
        self.last_finding: AgentFinding | None = None

    async def run(self, context: AgentContext) -> InvestigationState:
        if not isinstance(context, AgentContext):
            raise TypeError("engine capability agent requires AgentContext")
        self.last_finding = interpret_validated_result(self.result, capability=self.capability)
        return context.state


class GraphIntelligenceAgent(EngineCapabilityAgent):
    def __init__(self, result: object) -> None:
        super().__init__("graph_intelligence", result)


class PatternIntelligenceAgent(EngineCapabilityAgent):
    def __init__(self, result: object) -> None:
        super().__init__("pattern_analysis", result)


class FinancialIntelligenceAgent(EngineCapabilityAgent):
    def __init__(self, result: object) -> None:
        super().__init__("financial_analysis", result)


class TimelineIntelligenceAgent(EngineCapabilityAgent):
    def __init__(self, result: object) -> None:
        super().__init__("timeline", result)


class ForecastingAgent(EngineCapabilityAgent):
    def __init__(self, result: object) -> None:
        super().__init__("forecasting", result)


class LeadRankingAgent(EngineCapabilityAgent):
    def __init__(self, result: object) -> None:
        super().__init__("lead_ranking", result)


__all__ = [
    "AgentFinding", "EngineCapabilityAgent", "ForecastingAgent", "FinancialIntelligenceAgent",
    "GraphIntelligenceAgent", "LeadRankingAgent", "PatternIntelligenceAgent", "TimelineIntelligenceAgent",
    "interpret_validated_result",
]
