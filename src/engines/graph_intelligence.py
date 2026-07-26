"""Deterministic graph projection and bounded query helpers.

Neo4j is a projection/query store; Catalyst logical records remain authoritative.
This module owns graph-shaped records and traversal limits without importing a
Neo4j driver or allowing arbitrary Cypher. The optional client is an adapter
boundary for a later persistence integration.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, Literal
from uuid import UUID

from src.domain.enums import EntityType, RelationshipType
from src.domain.models import Entity, FIR, Relationship, to_record
from src.shared.errors import ApplicationError

MAX_TRAVERSAL_DEPTH = 5
GRAPH_LABEL_FOR_ENTITY = {
    EntityType.DIGITAL_EVIDENCE: "Evidence",
}



async def neo4j_health_check(client: object) -> bool:
    """Probe only the fixed health query through the validated adapter boundary."""

    try:
        result = await client.read("RETURN 1 AS health")
    except Exception:
        return False
    return bool(result)

class GraphQueryError(ApplicationError, ValueError):
    """A graph query violates the bounded, typed query contract."""


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    labels: frozenset[str]
    properties: dict[str, object]


@dataclass(frozen=True)
class GraphEdge:
    relationship_id: str
    source_id: str
    target_id: str
    relationship_type: str
    properties: dict[str, object]


@dataclass(frozen=True)
class GraphSubgraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    start_id: str
    max_depth: int


@dataclass(frozen=True)
class ProjectionSummary:
    nodes_total: int
    edges_total: int
    node_ids: tuple[str, ...] = field(default_factory=tuple)
    relationship_ids: tuple[str, ...] = field(default_factory=tuple)


class GraphProjection:
    """In-memory projection contract used by local tests and offline development.

    Upserts are keyed by Catalyst IDs, so replaying the same snapshot is
    idempotent. A production adapter may persist the same records through the
    existing ``Neo4jClient`` boundary without changing query semantics.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}

    @property
    def nodes(self) -> tuple[GraphNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    @property
    def edges(self) -> tuple[GraphEdge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def project(
        self,
        *,
        firs: Iterable[FIR] = (),
        entities: Iterable[Entity] = (),
        relationships: Iterable[Relationship] = (),
    ) -> ProjectionSummary:
        """Upsert one authoritative snapshot and return stable projection counts."""

        for fir in firs:
            self.upsert_fir(fir)
        for entity in entities:
            self.upsert_entity(entity)
        for relationship in relationships:
            self.upsert_relationship(relationship)
        return ProjectionSummary(
            nodes_total=len(self._nodes),
            edges_total=len(self._edges),
            node_ids=tuple(sorted(self._nodes)),
            relationship_ids=tuple(sorted(self._edges)),
        )

    def upsert_fir(self, fir: FIR) -> GraphNode:
        properties = to_record(fir)
        properties["node_id"] = str(fir.fir_id)
        properties["fir_id"] = str(fir.fir_id)
        return self._upsert_node(str(fir.fir_id), "FIR", properties)

    def upsert_entity(self, entity: Entity) -> GraphNode:
        label = GRAPH_LABEL_FOR_ENTITY.get(entity.entity_type, entity.entity_type.value)
        properties = to_record(entity)
        properties["node_id"] = str(entity.entity_id)
        properties["entity_id"] = str(entity.entity_id)
        return self._upsert_node(str(entity.entity_id), label, properties, additional_labels=("Entity",))

    def upsert_relationship(self, relationship: Relationship) -> GraphEdge:
        properties = to_record(relationship)
        properties["relationship_id"] = str(relationship.relationship_id)
        properties["evidence_fir_ids"] = [str(value) for value in relationship.evidence_fir_ids]
        edge = GraphEdge(
            relationship_id=str(relationship.relationship_id),
            source_id=str(relationship.source_entity_id),
            target_id=str(relationship.target_entity_id),
            relationship_type=relationship.relationship_type.value,
            properties=properties,
        )
        self._edges[edge.relationship_id] = edge
        return edge

    def traverse(
        self,
        start_id: UUID | str,
        *,
        max_depth: int = 2,
        relationship_types: Iterable[RelationshipType | str] | None = None,
        direction: Literal["out", "in", "both"] = "both",
    ) -> GraphSubgraph:
        """Return a bounded subgraph; arbitrary Cypher/depth is not accepted."""

        depth = _validate_depth(max_depth)
        start = str(start_id)
        if start not in self._nodes:
            raise GraphQueryError("GRAPH_NODE_NOT_FOUND", "The traversal start node is not projected.")
        if direction not in {"out", "in", "both"}:
            raise GraphQueryError("GRAPH_INVALID_DIRECTION", "Traversal direction is invalid.")
        allowed = _relationship_filter(relationship_types)
        distances = {start: 0}
        queue: deque[str] = deque([start])
        selected_edges: dict[str, GraphEdge] = {}
        while queue:
            current = queue.popleft()
            if distances[current] >= depth:
                continue
            for edge in self._edges.values():
                if allowed is not None and edge.relationship_type not in allowed:
                    continue
                neighbor = _neighbor(edge, current, direction)
                if neighbor is None:
                    continue
                selected_edges[edge.relationship_id] = edge
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        nodes = tuple(self._nodes[node_id] for node_id in sorted(distances))
        edges = tuple(selected_edges[key] for key in sorted(selected_edges))
        return GraphSubgraph(nodes=nodes, edges=edges, start_id=start, max_depth=depth)

    def shortest_path(
        self,
        start_id: UUID | str,
        target_id: UUID | str,
        *,
        max_depth: int = 5,
    ) -> tuple[GraphEdge, ...] | None:
        """Find a shortest bounded path and return its evidence-bearing edges."""

        depth = _validate_depth(max_depth)
        start, target = str(start_id), str(target_id)
        if start not in self._nodes or target not in self._nodes:
            raise GraphQueryError("GRAPH_NODE_NOT_FOUND", "Both path endpoints must be projected.")
        queue: deque[str] = deque([start])
        distance = {start: 0}
        previous: dict[str, tuple[str, GraphEdge]] = {}
        while queue:
            current = queue.popleft()
            if current == target:
                break
            if distance[current] >= depth:
                continue
            for edge in self._edges.values():
                neighbor = edge.target_id if edge.source_id == current else None
                if neighbor is None and edge.target_id == current:
                    neighbor = edge.source_id
                if neighbor is None or neighbor in distance:
                    continue
                distance[neighbor] = distance[current] + 1
                previous[neighbor] = (current, edge)
                queue.append(neighbor)
        if target not in distance:
            return None
        path: list[GraphEdge] = []
        current = target
        while current != start:
            parent, edge = previous[current]
            path.append(edge)
            current = parent
        path.reverse()
        return tuple(path)

    def _upsert_node(
        self,
        node_id: str,
        label: str,
        properties: dict[str, object],
        *,
        additional_labels: tuple[str, ...] = (),
    ) -> GraphNode:
        prior = self._nodes.get(node_id)
        labels = frozenset(set(prior.labels if prior else ()) | {label} | set(additional_labels))
        node = GraphNode(node_id=node_id, labels=labels, properties=properties)
        self._nodes[node_id] = node
        return node


def _validate_depth(max_depth: int) -> int:
    if isinstance(max_depth, bool) or not isinstance(max_depth, int) or not 0 <= max_depth <= MAX_TRAVERSAL_DEPTH:
        raise GraphQueryError(
            "GRAPH_DEPTH_LIMIT",
            f"Graph traversal depth must be an integer between 0 and {MAX_TRAVERSAL_DEPTH}.",
        )
    return max_depth


def _relationship_filter(values: Iterable[RelationshipType | str] | None) -> frozenset[str] | None:
    if values is None:
        return None
    try:
        return frozenset(value.value if isinstance(value, RelationshipType) else RelationshipType(value).value for value in values)
    except ValueError as exc:
        raise GraphQueryError("GRAPH_INVALID_RELATIONSHIP", "Relationship type is not in the locked vocabulary.") from exc


def _neighbor(edge: GraphEdge, current: str, direction: str) -> str | None:
    if direction in {"out", "both"} and edge.source_id == current:
        return edge.target_id
    if direction in {"in", "both"} and edge.target_id == current:
        return edge.source_id
    return None


# P13 bounded intelligence API. The import is lazy so this projection module
# remains usable as an independent boundary and avoids a circular import.
def analyze_graph(*args: object, **kwargs: object) -> object:
    from .graph_analysis import analyze_graph as implementation
    return implementation(*args, **kwargs)


def __getattr__(name: str) -> object:
    if name in {"CentralitySignal", "CommunitySignal", "GraphIntelligenceResult", "GraphPathSignal"}:
        from . import graph_analysis
        return getattr(graph_analysis, name)
    raise AttributeError(name)
