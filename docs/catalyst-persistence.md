# Catalyst Data Store persistence

This document describes the repository boundary added for Catalyst Data Store. Repository code uses `DataStorePort` only; Catalyst SDK/network behavior remains behind `CatalystDataStoreAdapter` and an explicitly injected `ExternalTransport`. External Catalyst access is still disabled unless `CATALYST_EXTERNAL_ENABLED=true` and a validated transport is supplied.

## Runtime selection

`main.build_api_application()` preserves local behavior by selecting `LocalCheckpointStore` unless `Settings.app_env == "catalyst"`. In Catalyst mode it constructs:

```text
CatalystDataStoreAdapter
  -> CatalystRepositorySet
  -> CatalystCheckpointStore
  -> InvestigationService
```

`catalyst_transport` is an optional typed injection on `build_api_application()`/`create_app()` for deployment and tests. No Catalyst client is created implicitly. Neo4j remains a separate projection/query boundary and is not replaced by these repositories.

## Logical table inventory

| Logical table | Repository | Key used by the DataStore boundary | Where it is used |
|---|---|---|---|
| `engine_runs` | `EngineRunRepository` | `run_id` | Typed CRUD/save boundary for engine execution records. |
| `evidence_provenance` | `EvidenceProvenanceRepository` | `provenance_id` | Typed CRUD/save boundary for source/provenance records. |
| `firs` | `FIRRepository` | `fir_id` | Typed CRUD/save boundary for FIR records. |
| `entities` | `EntityRepository` | `entity_id` | Typed CRUD/save boundary for entity records. |
| `fir_entities` | `FIREntityLinkRepository` | `fir_id:entity_id:role` | Typed CRUD/save boundary for FIR/entity links. |
| `relationships` | `RelationshipRepository` | `relationship_id` | Typed CRUD/save boundary for relationship records. Neo4j projection behavior is unchanged. |
| `investigations` | `InvestigationRepository` | `investigation_id` | Normalized projection written after every successful Catalyst checkpoint save. |
| `investigation_evidence` | `InvestigationEvidenceRepository` | `investigation_id:entity_id:fir_id` | Normalized rows written from the P09 aggregate evidence collection after every Catalyst checkpoint save. |
| `investigation_timeline` | `InvestigationTimelineRepository` | `timeline_id` | Normalized timeline rows written from the P09 aggregate after every Catalyst checkpoint save. |
| `intelligence_cards` | `IntelligenceCardRepository` plus `CatalystCardStore` | `card_id:v{version}` for active `CardRecord` envelopes | `CatalystCardStore` preserves the existing synchronous `CardStore` contract for `CardService` and `ProactiveAlertService`; the async repository is also directly available. The row `data` JSON contains the complete active `CardRecord` envelope so provenance, status, and version history survive a round trip. |
| `audit_logs` | `AuditLogRepository` | `{investigation_id}:v{state_version}` | Normalized rows written from P09 `AuditMetadata` after every Catalyst checkpoint save. |

The repository set is defined in `src/adapters/catalyst/repositories.py` and exports the exact table names in `LOGICAL_CATALYST_TABLES`. Generic CRUD is available through every table repository as `get`, `create`, `update`, `upsert`, `delete`, and `list`.

## Checkpoints are separate

`investigation_checkpoints` is an application checkpoint resource, not one of the 11 normalized logical tables. It stores the complete versioned `InvestigationState` required to restore notes, hypotheses, leads, graph view, health, and audit metadata without changing the existing P09 API behavior.

In Catalyst mode, `CatalystCheckpointStore` first writes the checkpoint and then projects the normalized investigation, evidence, timeline, and audit rows. The checkpoint remains the complete aggregate source for restoration; normalized rows support table-oriented access and reporting. The DataStore port has no transaction primitive, so deployment validation must confirm the desired failure/retry behavior if a projection write fails after a checkpoint write.

## Compatibility mappings

### Investigations

The locked normalized investigation status vocabulary predates P09 workspace lifecycle values. The normalized projection maps `CREATED` to `OPEN` and `ARCHIVED` to `CLOSED`; the exact lifecycle value remains in `investigation_checkpoints`. Other compatible values are written unchanged.

### Audit logs

The P09 aggregate audit entry is mapped to the locked audit table fields as follows:

```text
AuditMetadata.timestamp      -> audit_logs.timestamp
AuditMetadata.officer_id     -> audit_logs.user_id
authorization.role           -> audit_logs.user_role
AuditMetadata.action         -> audit_logs.action
"investigation"             -> audit_logs.resource_type
AuditMetadata.resource_id    -> audit_logs.resource_id
request_id/state_version     -> audit_logs.details
AuditMetadata.record_hash    -> audit_logs.hash_chain
AuditMetadata.previous_hash  -> audit_logs.prev_hash
```

The logical table's `log_id BIGSERIAL` is left to the physical Catalyst/table adapter; the repository uses a deterministic external key for idempotent projection. P09 actions outside the legacy table's small action vocabulary are intentionally normalized to `UPDATE`.

### Intelligence cards

The active card model has 15 lowercase `CardType` values while the legacy logical table reference lists five uppercase values. The repository does not silently discard the additional P14 card types: it writes the active lowercase type and complete `CardRecord` envelope into `intelligence_cards.data`. The Catalyst physical schema must reconcile/extend its card-type constraint before deployment. This is an explicit compatibility gap, not a claim that the locked PostgreSQL reference DDL is directly deployable to Catalyst.

## Validation scope

The repository tests use `LocalDataStore` as a deterministic `DataStorePort` double. They verify exact resource names, CRUD behavior, normalized P09 writes, card round trips, local-mode preservation, and Catalyst-mode checkpoint selection. No live Catalyst Data Store, Catalyst SDK, credentials, PostgreSQL extensions, vector index, or Catalyst physical DDL compatibility is claimed.
