"""Logical schema mapping metadata for Catalyst compatibility review.

The SQL in database-schema.md is a logical reference. This module deliberately does
not execute DDL, extensions, triggers, partial indexes, or PostgreSQL-only syntax.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.errors import ApplicationError


LOGICAL_TABLE_FIELDS: dict[str, frozenset[str]] = {
    "firs": frozenset(
        {
            "fir_id", "fir_number", "ps_code", "district", "crime_date", "registration_date",
            "ipc_sections", "crime_category", "crime_subtype", "narrative_en", "narrative_kn",
            "narrative_vec", "status", "priority", "modus_operandi", "complainant_name",
            "io_officer_id", "created_at", "updated_at",
        }
    ),
    "entities": frozenset(
        {
            "entity_id", "entity_type", "entity_value", "canonical_value", "attributes", "first_seen",
            "last_seen", "risk_score", "merged_into", "created_at",
        }
    ),
    "fir_entities": frozenset(
        {"fir_id", "entity_id", "role", "confidence", "extraction_method", "extracted_at"}
    ),
    "relationships": frozenset(
        {
            "relationship_id", "source_entity_id", "target_entity_id", "relationship_type", "strength",
            "evidence_fir_ids", "discovered_at", "discovery_method", "verified", "verified_by",
            "verified_at", "expires_at",
        }
    ),
    "investigations": frozenset(
        {
            "investigation_id", "title", "description", "primary_fir_id", "status", "owner_id",
            "team_ids", "hypothesis", "priority", "created_at", "updated_at", "closed_at",
        }
    ),
    "investigation_evidence": frozenset(
        {"investigation_id", "entity_id", "fir_id", "note", "pinned_by", "pinned_at", "tags", "relevance_score"}
    ),
    "investigation_timeline": frozenset(
        {
            "timeline_id", "investigation_id", "event_time", "event_type", "description", "source_fir_id",
            "source_entity_id", "confidence", "created_by", "created_at",
        }
    ),
    "engine_runs": frozenset(
        {"run_id", "engine_name", "tool_id", "input_hash", "status", "output_ref", "source_snapshot", "computed_at", "expires_at", "audit_metadata"}
    ),
    "evidence_provenance": frozenset(
        {"provenance_id", "run_id", "claim_id", "source_type", "source_id", "calculation", "permission_scope", "contradiction_refs", "confidence", "validated_at", "validator_version"}
    ),
    "intelligence_cards": frozenset(
        {"card_id", "card_type", "subject_entity_id", "subject_fir_id", "data", "generated_at", "valid_until", "version", "generated_by", "superseded_by"}
    ),
    "audit_logs": frozenset(
        {"log_id", "timestamp", "user_id", "user_role", "action", "resource_type", "resource_id", "details", "ip_address", "session_id", "hash_chain", "prev_hash"}
    ),
}

LOGICAL_ONLY_POSTGRES_FEATURES = (
    "uuid-ossp extension",
    "pgcrypto extension",
    "vector extension",
    "pg_trgm extension",
    "PostgreSQL UUID[]/JSONB/VECTOR/INET types",
    "PostgreSQL generated/partial indexes",
    "NOW()-based partial index predicates",
    "audit hash-chain trigger and PL/pgSQL function",
    "COALESCE expression primary key",
)


@dataclass(frozen=True)
class CatalystCompatibilityReport:
    table: str
    unknown_fields: tuple[str, ...]
    logical_only_features: tuple[str, ...] = LOGICAL_ONLY_POSTGRES_FEATURES
    deployable_without_validation: bool = False


class SchemaMappingError(ApplicationError, ValueError):
    """The logical record does not map to a known locked table field."""


def validate_logical_fields(table: str, fields: set[str] | frozenset[str]) -> CatalystCompatibilityReport:
    allowed = LOGICAL_TABLE_FIELDS.get(table)
    if allowed is None:
        raise SchemaMappingError("SCHEMA_UNKNOWN_TABLE", "Unknown logical table.", details={"table": table})
    unknown = tuple(sorted(set(fields) - allowed))
    if unknown:
        raise SchemaMappingError(
            "SCHEMA_UNKNOWN_FIELDS",
            "Record contains fields outside the locked logical table mapping.",
            details={"table": table, "fields": list(unknown)},
        )
    return CatalystCompatibilityReport(table=table, unknown_fields=unknown)


def catalyst_mapping_is_validated(report: CatalystCompatibilityReport) -> bool:
    """Always false until deployment-specific Catalyst behavior is verified."""

    return report.deployable_without_validation
