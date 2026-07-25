from datetime import datetime, timezone
import json
import re
import unittest
from uuid import uuid4

from data.generator import generate_fixture
from src.domain.enums import (
    CardType,
    EntityType,
    FIRStatus,
    RelationshipType,
    SCHEMA_EXTENSION_ENTITY_TYPES,
)
from src.domain.models import (
    Entity,
    FIR,
    FIREntityLink,
    IntelligenceCard,
    ModelValidationError,
    Relationship,
)
from src.domain.ontology import canonicalize, schema_entity_type, validate_relationship_endpoints
from src.domain.schema_mapping import (
    LOGICAL_TABLE_FIELDS,
    catalyst_mapping_is_validated,
    validate_logical_fields,
)


UTC = timezone.utc


class VocabularyTests(unittest.TestCase):
    def test_schema_entity_vocabulary_is_exact_and_extensions_are_rejected(self) -> None:
        self.assertEqual(len(EntityType), 15)
        self.assertEqual(len(RelationshipType), 20)
        self.assertEqual(len(CardType), 5)
        self.assertEqual(set(SCHEMA_EXTENSION_ENTITY_TYPES), {"IMEI", "Evidence", "District"})
        with self.assertRaises(ValueError):
            schema_entity_type("Evidence")
        self.assertEqual(schema_entity_type("Person"), EntityType.PERSON)

    def test_canonical_forms_and_relationship_endpoints(self) -> None:
        self.assertEqual(
            canonicalize(EntityType.PERSON, "Synthetic Person", attributes={"dob": "1990-01-01", "father_name": "Synthetic Parent"}),
            "SYNTHETIC PERSON|1990-01-01|SYNTHETIC PARENT",
        )
        self.assertEqual(canonicalize(EntityType.PHONE, "+91 0000000001"), "+910000000001")
        self.assertEqual(canonicalize(EntityType.UPI, "Synthetic@DEMO"), "synthetic@demo")
        validate_relationship_endpoints(RelationshipType.ACCUSED_IN, EntityType.PERSON, EntityType.FIR)
        with self.assertRaises(ValueError):
            validate_relationship_endpoints(RelationshipType.ACCUSED_IN, EntityType.PHONE, EntityType.FIR)


class ModelConstraintTests(unittest.TestCase):
    def test_fir_validates_status_priority_and_vector_dimension(self) -> None:
        common = {
            "fir_number": "KA/BLR-C/042/2026/000001",
            "ps_code": "KA-BLR-C-042",
            "district": "Bangalore City",
            "crime_date": datetime(2026, 1, 1, tzinfo=UTC),
            "registration_date": datetime(2026, 1, 1, 1, tzinfo=UTC),
            "ipc_sections": (379,),
            "crime_category": "Vehicle Theft",
        }
        fir = FIR(**common, status="OPEN", priority="HIGH")
        self.assertEqual(fir.status, FIRStatus.OPEN)
        with self.assertRaises(ModelValidationError):
            FIR(**common, narrative_vec=(0.0,))

    def test_verified_relationship_requires_fir_provenance_and_verifier(self) -> None:
        with self.assertRaises(ModelValidationError):
            Relationship(uuid4(), uuid4(), RelationshipType.CALLED, verified=True)

    def test_evidence_card_requires_subject(self) -> None:
        with self.assertRaises(ModelValidationError):
            IntelligenceCard(CardType.HOTSPOT, {}, datetime(2026, 2, 1, tzinfo=UTC))

    def test_logical_mapping_rejects_unknown_fields_and_is_not_deployable(self) -> None:
        report = validate_logical_fields("firs", {"fir_id", "status"})
        self.assertEqual(report.unknown_fields, ())
        self.assertFalse(catalyst_mapping_is_validated(report))
        self.assertIn("firs", LOGICAL_TABLE_FIELDS)
        with self.assertRaises(Exception):
            validate_logical_fields("firs", {"not_a_locked_field"})


class SyntheticFixtureTests(unittest.TestCase):
    def test_fixture_is_reproducible_and_schema_shaped(self) -> None:
        first = generate_fixture(6, seed=42, year=2026)
        second = generate_fixture(6, seed=42, year=2026)
        self.assertEqual(first.sha256(), second.sha256())
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(len(first.firs), 6)
        self.assertGreaterEqual(len(first.entities), 6 * 4)
        self.assertEqual(len(first.fir_entities), 6 * 4)
        self.assertTrue(first.relationships)
        for fir in first.firs:
            self.assertRegex(fir.fir_number, r"^KA/[A-Z-]+/\d{3}/2026/\d{6}$")
            self.assertRegex(fir.ps_code, r"^KA-(?:[A-Z]+-[A-Z]|[A-Z]+)-\d{3}$")
            self.assertIn("SYNTHETIC-DEMO-ONLY", fir.narrative_en or "")
        for relationship in first.relationships:
            self.assertTrue(relationship.evidence_fir_ids)

    def test_different_seed_changes_fixture(self) -> None:
        self.assertNotEqual(generate_fixture(2, seed=1).sha256(), generate_fixture(2, seed=2).sha256())

    def test_fixture_json_is_serializable(self) -> None:
        fixture = generate_fixture(1)
        parsed = json.loads(fixture.canonical_json())
        self.assertEqual(len(parsed["firs"]), 1)
        self.assertTrue(parsed["firs"][0]["fir_number"].startswith("KA/"))


if __name__ == "__main__":
    unittest.main()
