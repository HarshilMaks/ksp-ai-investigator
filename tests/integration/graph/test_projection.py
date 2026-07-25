from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from data.generator import generate_fixture
from src.engines.graph_intelligence import (
    MAX_TRAVERSAL_DEPTH,
    GraphProjection,
    GraphQueryError,
    neo4j_health_check,
)
from src.shared.config import load_settings
from src.adapters.neo4j import Neo4jClient


ROOT = Path(__file__).resolve().parents[3]


class GraphProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = generate_fixture(count=8, seed=20260725, year=2026)
        self.graph = GraphProjection()
        self.first = self.graph.project(
            firs=self.fixture.firs,
            entities=self.fixture.entities,
            relationships=self.fixture.relationships,
        )

    def test_projection_is_idempotent_for_same_authoritative_snapshot(self) -> None:
        second = self.graph.project(
            firs=self.fixture.firs,
            entities=self.fixture.entities,
            relationships=self.fixture.relationships,
        )
        self.assertEqual(self.first, second)
        self.assertEqual(len(self.fixture.firs) + len(self.fixture.entities), self.first.nodes_total)
        self.assertEqual(len(self.fixture.relationships), self.first.edges_total)

    def test_relationship_provenance_and_verification_survive_projection(self) -> None:
        source = next(relationship for relationship in self.fixture.relationships if relationship.evidence_fir_ids)
        edge = next(edge for edge in self.graph.edges if edge.relationship_id == str(source.relationship_id))
        self.assertEqual(source.relationship_type.value, edge.relationship_type)
        self.assertEqual([str(value) for value in source.evidence_fir_ids], edge.properties["evidence_fir_ids"])
        self.assertEqual(source.verified, edge.properties["verified"])
        if source.verified:
            self.assertIsNotNone(edge.properties["verified_by"])
            self.assertIsNotNone(edge.properties["verified_at"])

    def test_bounded_traversal_and_path_return_citable_edges(self) -> None:
        relationship = self.fixture.relationships[0]
        result = self.graph.traverse(relationship.source_entity_id, max_depth=2)
        self.assertIn(str(relationship.source_entity_id), {node.node_id for node in result.nodes})
        self.assertTrue(any(edge.relationship_id == str(relationship.relationship_id) for edge in result.edges))
        path = self.graph.shortest_path(relationship.source_entity_id, relationship.target_entity_id, max_depth=1)
        self.assertIsNotNone(path)
        self.assertEqual(str(relationship.relationship_id), path[0].relationship_id)

    def test_depth_and_relationship_vocabulary_are_bounded(self) -> None:
        with self.assertRaises(GraphQueryError):
            self.graph.traverse(self.fixture.entities[0].entity_id, max_depth=MAX_TRAVERSAL_DEPTH + 1)
        with self.assertRaises(GraphQueryError):
            self.graph.traverse(self.fixture.entities[0].entity_id, relationship_types=["UNCONTROLLED_QUERY"])

    def test_digital_evidence_uses_graph_compatibility_label(self) -> None:
        evidence = next((entity for entity in self.fixture.entities if entity.entity_type.value == "DigitalEvidence"), None)
        if evidence is not None:
            node = next(node for node in self.graph.nodes if node.node_id == str(evidence.entity_id))
            self.assertIn("Evidence", node.labels)


class GraphDeploymentContractTests(unittest.TestCase):
    def test_schema_contains_locked_labels_relationships_and_idempotent_ddl(self) -> None:
        schema = (ROOT / "appsail/neo4j/import/schema.cypher").read_text()
        for label in (
            "FIR", "Person", "Phone", "Vehicle", "UPI", "BankAccount", "Location",
            "CCTV", "Weapon", "Organization", "Document", "DigitalEvidence", "Evidence",
            "Address", "PoliceStation", "CrimeCategory",
        ):
            self.assertIn(f"(n:{label})", schema)
        for relationship_type in (
            "ACCUSED_IN", "VICTIM_IN", "WITNESS_IN", "OWNS_PHONE", "OWNS_VEHICLE",
            "OWNS_ACCOUNT", "LOCATED_AT", "CAPTURED_BY", "CALLED", "TRANSACTED_WITH",
            "CO_ACCUSED_WITH", "SHARES_PHONE_WITH", "SHARES_VEHICLE_WITH", "SHARES_UPI_WITH",
            "FINANCIAL_FLOW", "TEMPORAL_PROXIMITY", "SAME_MODUS_OPERANDI", "BELONGS_TO_GANG",
            "JURISDICTION_OF", "CATEGORIZED_AS",
        ):
            self.assertIn(relationship_type, schema)
        self.assertIn("IF NOT EXISTS", schema)

    def test_app_sail_assets_preserve_ports_and_private_browser(self) -> None:
        dockerfile = (ROOT / "appsail/neo4j/Dockerfile").read_text()
        config = (ROOT / "appsail/neo4j/neo4j.conf").read_text()
        self.assertIn("neo4j:5.26.0-community", dockerfile)
        self.assertIn("EXPOSE 7687", dockerfile)
        self.assertIn("0.0.0.0:7687", config)
        self.assertIn("127.0.0.1:7474", config)
        self.assertNotIn("EXPOSE 7474", dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)
        self.assertIn("memory.heap.max_size=512m", config)

    def test_disabled_default_health_check_reports_unavailable(self) -> None:
        client = Neo4jClient(load_settings({"APP_ENV": "test"}))
        self.assertFalse(asyncio.run(neo4j_health_check(client)))


if __name__ == "__main__":
    unittest.main()
