"""Bounded graph intelligence facts over an already projected graph."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable

from .intelligence_types import EngineMetadata, SourceEvidence, Uncertainty

MAX_GRAPH_NODES = 500
MAX_GRAPH_EDGES = 1_000
MAX_GRAPH_HOPS = 5


@dataclass(frozen=True)
class CentralitySignal:
    node_id: str
    degree: int
    normalized_score: float
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class CommunitySignal:
    community_id: str
    member_ids: tuple[str, ...]
    density: float
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class GraphPathSignal:
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class GraphIntelligenceResult:
    centrality: tuple[CentralitySignal, ...]
    communities: tuple[CommunitySignal, ...]
    paths: tuple[GraphPathSignal, ...]
    metadata: EngineMetadata
    uncertainty: Uncertainty


def analyze_graph(
    nodes: Iterable[Any],
    edges: Iterable[Any],
    *,
    max_hops: int = 3,
    max_candidates: int = 100,
) -> GraphIntelligenceResult:
    """Compute deterministic degree/community/path facts with hard bounds."""

    if not isinstance(max_hops, int) or isinstance(max_hops, bool) or not 0 <= max_hops <= MAX_GRAPH_HOPS:
        raise ValueError(f"max_hops must be an integer between 0 and {MAX_GRAPH_HOPS}")
    if not isinstance(max_candidates, int) or isinstance(max_candidates, bool) or not 1 <= max_candidates <= MAX_GRAPH_NODES:
        raise ValueError(f"max_candidates must be between 1 and {MAX_GRAPH_NODES}")
    node_map = {node.node_id: node for node in nodes}
    edge_list = sorted(edges, key=lambda edge: edge.relationship_id)
    if len(node_map) > MAX_GRAPH_NODES or len(edge_list) > MAX_GRAPH_EDGES:
        raise ValueError("graph input exceeds bounded intelligence limits")
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_map}
    edge_by_pair: dict[tuple[str, str], GraphEdge] = {}
    for edge in edge_list:
        if edge.source_id not in node_map or edge.target_id not in node_map:
            continue
        adjacency[edge.source_id].add(edge.target_id)
        adjacency[edge.target_id].add(edge.source_id)
        edge_by_pair.setdefault((edge.source_id, edge.target_id), edge)
        edge_by_pair.setdefault((edge.target_id, edge.source_id), edge)
    denominator = max(1, len(node_map) - 1)
    centrality = tuple(
        CentralitySignal(
            node_id=node_id,
            degree=len(adjacency[node_id]),
            normalized_score=round(len(adjacency[node_id]) / denominator, 6),
            evidence=_edge_evidence(node_id, edge_list),
        )
        for node_id in sorted(node_map, key=lambda value: (-len(adjacency[value]), value))[:max_candidates]
    )
    communities = _communities(adjacency, edge_by_pair, max_candidates)
    paths = _bounded_paths(adjacency, edge_by_pair, max_hops, max_candidates)
    metadata = EngineMetadata(
        engine="graph_intelligence",
        algorithm="bounded_degree_components_paths",
        version="p13.1",
        parameters=(("max_hops", max_hops), ("max_candidates", max_candidates)),
        input_count=len(node_map) + len(edge_list),
    )
    return GraphIntelligenceResult(
        centrality=centrality,
        communities=communities,
        paths=paths,
        metadata=metadata,
        uncertainty=Uncertainty("observed_graph_only", 1.0 if node_map else 0.0, ("No unobserved relationships are inferred.",)),
    )


def _edge_evidence(node_id: str, edges: list[Any]) -> tuple[SourceEvidence, ...]:
    values: dict[str, SourceEvidence] = {}
    for edge in edges:
        if node_id not in {edge.source_id, edge.target_id}:
            continue
        for source_id in edge.properties.get("evidence_fir_ids", ()):
            values[str(source_id)] = SourceEvidence(str(source_id), "FIR")
    return tuple(values[key] for key in sorted(values))


def _communities(adjacency: dict[str, set[str]], edge_by_pair: dict[tuple[str, str], Any], limit: int) -> tuple[CommunitySignal, ...]:
    remaining = set(adjacency)
    output: list[CommunitySignal] = []
    number = 0
    while remaining and len(output) < limit:
        start = min(remaining)
        queue = [start]
        members: list[str] = []
        remaining.remove(start)
        while queue:
            current = queue.pop(0)
            members.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        member_set = set(members)
        possible = len(members) * (len(members) - 1) / 2
        actual = sum(1 for (source, target) in edge_by_pair if source < target and source in member_set and target in member_set)
        evidence = tuple(sorted({source for member in members for source in _edge_evidence(member, list(edge_by_pair.values()))}, key=lambda item: item.source_id))
        output.append(CommunitySignal(f"community-{number}", tuple(sorted(members)), round(actual / possible, 6) if possible else 0.0, evidence))
        number += 1
    return tuple(output)


def _bounded_paths(adjacency: dict[str, set[str]], edge_by_pair: dict[tuple[str, str], Any], max_hops: int, limit: int) -> tuple[GraphPathSignal, ...]:
    if max_hops == 0:
        return ()
    output: list[GraphPathSignal] = []
    for start in sorted(adjacency):
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(start, (start,))])
        while queue and len(output) < limit:
            current, path = queue.popleft()
            if len(path) > 1:
                edge_ids = tuple(edge_by_pair[(left, right)].relationship_id for left, right in zip(path, path[1:]))
                evidence = tuple(sorted({source for left, right in zip(path, path[1:]) for source in _edge_evidence(left, [edge_by_pair[(left, right)]])}, key=lambda item: item.source_id))
                output.append(GraphPathSignal(path, edge_ids, evidence))
            if len(path) - 1 >= max_hops:
                continue
            for neighbor in sorted(adjacency[current]):
                if neighbor not in path:
                    queue.append((neighbor, path + (neighbor,)))
        if len(output) >= limit:
            break
    return tuple(output)


__all__ = ["CentralitySignal", "CommunitySignal", "GraphIntelligenceResult", "GraphPathSignal", "analyze_graph"]
