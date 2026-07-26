"""Ten deterministic synthetic scenario fixtures for CI and local demos."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable


@dataclass(frozen=True)
class ScenarioFixture:
    number: int
    name: str
    route: str
    persona: str
    opening_query: str
    engines: tuple[str, ...]
    cards: tuple[str, ...]
    citations: tuple[str, ...]
    proactive: bool = False
    fallback: str = "deterministic local fixture"

    def __post_init__(self) -> None:
        if not self.name or not self.engines or not self.cards or not self.citations:
            raise ValueError("scenario requires name, engines, cards, and citations")
        if any(not item.startswith("SYNTHETIC-") for item in self.citations):
            raise ValueError("scenario citations must be synthetic")
        if self.proactive and self.opening_query:
            raise ValueError("proactive scenarios must not require an opening query")

    def to_record(self) -> dict[str, object]:
        return asdict(self)


def build_scenarios(seed: int = 20260726) -> tuple[ScenarioFixture, ...]:
    prefix = f"SYNTHETIC-{seed}"
    raw = [
        (1, "Organized Vehicle Theft Ring", "deep", "IO", "Show linked vehicle theft FIRs", ("sql_retrieval", "graph_intelligence", "pattern_analysis", "behavioral_profiling", "search_ranking"), ("criminal_network", "offender_profile", "investigation_timeline", "lead"), False),
        (2, "Cybercrime Repeat Offender", "deep", "Analyst", "Profile the synthetic repeat offender escalation", ("sql_retrieval", "behavioral_profiling", "pattern_analysis", "graph_intelligence", "timeline"), ("offender_profile", "forecast", "reasoning_trace"), False),
        (3, "UPI Fraud Money Trail", "deep", "IO", "Trace the synthetic UPI money trail", ("financial_analysis", "graph_intelligence", "pattern_analysis", "sql_retrieval", "timeline"), ("financial_trail", "lead", "reasoning_trace"), False),
        (4, "Chain Snatching Hotspot Forecast", "deep", "DCP", "Review the synthetic 30-day hotspot forecast", ("forecasting", "pattern_analysis", "sql_retrieval"), ("crime_hotspot", "forecast", "sociological_insight"), False),
        (5, "Linked Robbery Hypothesis", "deep", "SHO", "Evaluate whether three synthetic robberies are connected", ("sql_retrieval", "graph_intelligence", "pattern_analysis", "behavioral_profiling", "timeline"), ("hypothesis", "reasoning_trace", "lead"), False),
        (6, "Proactive Alert New FIR Match", "signals", "IO", "", ("sql_retrieval", "graph_intelligence", "financial_analysis", "evidence_gate"), ("proactive_alert", "financial_trail", "reasoning_trace"), True),
        (7, "Entity Resolution Name Variants", "fast", "Analyst", "Show evidence for a synthetic entity match", ("entity_resolution", "graph_intelligence", "pattern_analysis", "evidence_gate"), ("entity_resolution", "offender_profile", "reasoning_trace"), False),
        (8, "Drug Network Discovery", "deep", "Analyst", "Expand the synthetic drug network", ("graph_intelligence", "financial_analysis", "pattern_analysis", "behavioral_profiling", "timeline"), ("criminal_network", "lead", "reasoning_trace"), False),
        (9, "Investigation Handover", "fast", "IO", "Generate a synthetic investigation handover", ("timeline", "graph_intelligence", "evidence_gate", "lead_ranking"), ("case_summary", "investigation_timeline", "evidence_summary", "hypothesis", "lead"), False),
        (10, "Strategic Intelligence Briefing", "deep", "SP", "Generate the synthetic district intelligence briefing", ("sql_retrieval", "forecasting", "pattern_analysis", "graph_intelligence", "behavioral_profiling", "financial_analysis"), ("case_summary", "forecast", "criminal_network", "sociological_insight"), False),
    ]
    return tuple(ScenarioFixture(number, name, route, persona, query, engines, cards, (f"{prefix}-SCENARIO-{number}-SOURCE",), proactive, "synthetic deterministic fallback") for number, name, route, persona, query, engines, cards, proactive in raw)


def scenario_digest(scenarios: Iterable[ScenarioFixture]) -> str:
    payload = json.dumps([scenario.to_record() for scenario in scenarios], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def primary_demo_order() -> tuple[int, ...]:
    return (3, 1, 6, 5, 4, 10)


__all__ = ["ScenarioFixture", "build_scenarios", "primary_demo_order", "scenario_digest"]
