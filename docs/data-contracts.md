# P04 Data Contracts and Synthetic Fixtures

> Derived from `.LOCK/database-schema.md`, `.LOCK/ontology.md`, and `.LOCK/crime-domain.md`. This document records implementation mapping only; it does not replace the locked documents.

## Contract boundary

- Catalyst Data Store remains authoritative for structured/vector records.
- Neo4j remains a projection/query store and is not written by P04.
- `src/domain/enums.py` accepts the exact entity, relationship, status, role, discovery, card, timeline, and audit vocabularies in the logical database schema.
- `src/domain/models.py` validates confidence values in `[0, 1]`, relationship strength in `[0, 1.5]`, 1024-dimensional FIR vectors when present, evidence targets, verified-relationship provenance, card subjects, and timezone-aware timestamps.
- `src/domain/ontology.py` provides deterministic canonical formatting and endpoint validation. It does not merge people or make identity decisions.
- Entity concepts recorded as domain extensions but not admitted by the current schema check constraint (`IMEI`, `Evidence`, `District`) are explicitly rejected by `schema_entity_type()` until a reviewed schema extension exists.

## Logical-to-Catalyst mapping

`src/domain/schema_mapping.py` contains field metadata for `firs`, `entities`, `fir_entities`, `relationships`, `investigations`, `investigation_evidence`, `investigation_timeline`, `engine_runs`, `evidence_provenance`, `intelligence_cards`, and `audit_logs`.

The PostgreSQL DDL remains a logical reference. P04 does not execute or claim compatibility for PostgreSQL extensions (`uuid-ossp`, `pgcrypto`, `vector`, `pg_trgm`), PostgreSQL-specific array/JSONB/VECTOR/INET types, partial indexes, `NOW()` predicates, the PL/pgSQL audit trigger, or expression-based primary keys. `CatalystCompatibilityReport.deployable_without_validation` remains `False` until deployment validation.

## Synthetic data policy

`data/generator/` uses seeded UUID5 identifiers, fixed timestamps, fictional names, invalid/synthetic vehicle prefixes, synthetic phone/UPI values, and `SYNTHETIC-DEMO-ONLY` narrative markers. `SyntheticFixture.sha256()` provides reproducibility evidence. Generated records are not real police records and do not establish legal, predictive, or benchmark claims.

## Fixture shape

`generate_fixture(count, seed, year)` returns:

```text
SyntheticFixture
├── firs
├── entities
├── fir_entities
└── relationships
```

Each generated relationship references at least one source FIR as evidence. P04 only constructs logical records; ingestion, persistence, graph projection, embeddings, and intelligence engines are later phases.

## P09 persistent investigation state

`src/domain/investigation_state.py` is the application workspace aggregate passed between the Investigation Service and future Runner boundary. It deliberately complements rather than replaces the logical `investigations` table contract: the P09 aggregate carries versioned evidence, notes, hypotheses, timeline events, leads, graph view state, health provenance, and audit metadata.

`src/services/checkpoints.py` defines the Catalyst-compatible checkpoint port. `LocalCheckpointStore` writes atomic versioned JSON plus a latest pointer so a new local service instance can resume state. `CatalystCheckpointStore` uses the existing `DataStorePort` with the same serialized contract. Checkpoint writes use optimistic version checks and reject stale or invalid versions.

Every P09 mutation goes through `InvestigationService`, which authorizes the officer, applies one synchronized state update, recalculates deterministic Investigation Health, increments the state version, and appends request/officer/version/hash audit metadata. The local P09 health policy reports evidence, timeline, network, financial, and witness coverage as bounded percentages, contradiction count, missing critical evidence, and metric-level source/calculation provenance. Thresholds are application policy and remain subject to later measured/product review.
