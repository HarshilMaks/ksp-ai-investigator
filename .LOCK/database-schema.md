# KSP InvestigateAI — Complete Database Schema
> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24


> Catalyst Data Store is authoritative for structured and vector data (pgvector HNSW); Neo4j 5 Community on AppSail is the graph projection/query store. The raw PostgreSQL DDL below is a logical reference mapping only: extensions, triggers, and syntax require Catalyst validation and are not guaranteed deployable Catalyst schema.

---

## Catalyst Data Store — Logical schema reference mapping

### Engine outputs and evidence provenance

The Catalyst Data Store remains authoritative for structured records and pgvector embeddings. Deterministic engines may materialize reusable outputs in `intelligence_cards` and Stratus; Neo4j is a projection/query store. Every materialized result and response claim needs provenance so the evidence gate can reproduce and qualify it.

```sql
CREATE TABLE engine_runs (
    run_id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engine_name         VARCHAR(80) NOT NULL,
    tool_id              VARCHAR(3) NOT NULL, -- T01-T23
    input_hash          VARCHAR(128) NOT NULL,
    status              VARCHAR(20) NOT NULL,
    output_ref          TEXT,
    source_snapshot     JSONB NOT NULL DEFAULT '{}',
    computed_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMP WITH TIME ZONE,
    audit_metadata      JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE evidence_provenance (
    provenance_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id              UUID REFERENCES engine_runs(run_id),
    claim_id            VARCHAR(128) NOT NULL,
    source_type         VARCHAR(40) NOT NULL, -- FIR, entity, relationship, computation
    source_id           VARCHAR(128) NOT NULL,
    calculation         JSONB NOT NULL DEFAULT '{}',
    permission_scope    JSONB NOT NULL DEFAULT '{}',
    contradiction_refs  JSONB NOT NULL DEFAULT '[]',
    confidence          REAL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    validated_at        TIMESTAMP WITH TIME ZONE,
    validator_version   VARCHAR(40)
);
```

`engine_runs` and `evidence_provenance` are logical reference mappings; Catalyst syntax, indexes, retention, and deployment behavior require validation. No provenance record establishes legal sufficiency or a final human decision.

### Extensions Required

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";          -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- trigram similarity
```

---

### Table: firs

The core table. Every First Information Report filed in Karnataka.

```sql
CREATE TABLE firs (
    fir_id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fir_number          VARCHAR(50) NOT NULL,
    ps_code             VARCHAR(20) NOT NULL,
    district            VARCHAR(100) NOT NULL,
    crime_date          TIMESTAMP WITH TIME ZONE NOT NULL,
    registration_date   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ipc_sections        INT[] NOT NULL DEFAULT '{}',
    crime_category      VARCHAR(100) NOT NULL,
    crime_subtype       VARCHAR(100),
    narrative_en        TEXT,
    narrative_kn        TEXT,
    narrative_vec       VECTOR(1024),
    status              VARCHAR(30) NOT NULL DEFAULT 'OPEN'
                        CHECK (status IN ('OPEN','UNDER_INVESTIGATION','CHARGESHEETED','CLOSED','REFERRED')),
    priority            VARCHAR(20) NOT NULL DEFAULT 'MEDIUM'
                        CHECK (priority IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    modus_operandi      JSONB DEFAULT '{}',
    complainant_name    VARCHAR(255),
    io_officer_id       UUID,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_fir_number UNIQUE (ps_code, fir_number, EXTRACT(YEAR FROM registration_date))
);

COMMENT ON TABLE firs IS 'First Information Reports - core crime records for Karnataka State Police';
COMMENT ON COLUMN firs.narrative_vec IS '1024-dim dense embedding from AlpEge/bge-m3-onnx-int8 (ONNX CPU)';
COMMENT ON COLUMN firs.modus_operandi IS 'Structured MO: {"method":"...","tools":[],"time":"...","target":"..."}';
```

---

### Table: entities

All resolved entities extracted from FIRs and external sources.

```sql
CREATE TABLE entities (
    entity_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type         VARCHAR(50) NOT NULL
                        CHECK (entity_type IN (
                            'Person','Phone','Vehicle','UPI','BankAccount',
                            'Location','CCTV','Weapon','Organization',
                            'Document','DigitalEvidence','Address',
                            'FIR','PoliceStation','CrimeCategory'
                        )),
    entity_value        TEXT NOT NULL,
    canonical_value     TEXT NOT NULL,
    attributes          JSONB NOT NULL DEFAULT '{}',
    first_seen          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    risk_score          REAL DEFAULT 0.0 CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    merged_into         UUID REFERENCES entities(entity_id),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE entities IS 'Canonical entity store - all nouns in the investigation domain';
COMMENT ON COLUMN entities.canonical_value IS 'Normalized form used for deduplication and resolution';
COMMENT ON COLUMN entities.merged_into IS 'If entity was merged as duplicate, points to surviving entity';
```

---

### Table: fir_entities

Junction table linking FIRs to entities with role and confidence.

```sql
CREATE TABLE fir_entities (
    fir_id              UUID NOT NULL REFERENCES firs(fir_id) ON DELETE CASCADE,
    entity_id           UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    role                VARCHAR(50) NOT NULL
                        CHECK (role IN (
                            'ACCUSED','VICTIM','WITNESS','COMPLAINANT',
                            'OWNER','SUSPECT','MENTIONED','EVIDENCE',
                            'LOCATION','WEAPON_USED','VEHICLE_USED'
                        )),
    confidence          REAL NOT NULL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    extraction_method   VARCHAR(50) NOT NULL DEFAULT 'MANUAL'
                        CHECK (extraction_method IN ('MANUAL','NER','REGEX','LOOKUP','INFERENCE')),
    extracted_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    PRIMARY KEY (fir_id, entity_id, role)
);

COMMENT ON TABLE fir_entities IS 'Links entities to FIRs with their role and extraction confidence';
```

---

### Table: relationships

Entity-to-entity relationships with strength and evidence.

```sql
CREATE TABLE relationships (
    relationship_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_entity_id    UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    target_entity_id    UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    relationship_type   VARCHAR(50) NOT NULL
                        CHECK (relationship_type IN (
                            'ACCUSED_IN','VICTIM_IN','WITNESS_IN',
                            'OWNS_PHONE','OWNS_VEHICLE','OWNS_ACCOUNT',
                            'LOCATED_AT','CAPTURED_BY','CALLED','TRANSACTED_WITH',
                            'CO_ACCUSED_WITH','SHARES_PHONE_WITH','SHARES_VEHICLE_WITH',
                            'SHARES_UPI_WITH','FINANCIAL_FLOW','TEMPORAL_PROXIMITY',
                            'SAME_MODUS_OPERANDI','BELONGS_TO_GANG',
                            'JURISDICTION_OF','CATEGORIZED_AS'
                        )),
    strength            REAL NOT NULL DEFAULT 1.0 CHECK (strength >= 0.0 AND strength <= 1.5),
    evidence_fir_ids    UUID[] NOT NULL DEFAULT '{}',
    discovered_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    discovery_method    VARCHAR(50) NOT NULL DEFAULT 'MANUAL'
                        CHECK (discovery_method IN ('MANUAL','COMPUTED','NER','CDR_ANALYSIS','FINANCIAL_ANALYSIS','PATTERN_MATCH')),
    verified            BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by         UUID,
    verified_at         TIMESTAMP WITH TIME ZONE,
    expires_at          TIMESTAMP WITH TIME ZONE,

    CONSTRAINT uq_relationship UNIQUE (source_entity_id, target_entity_id, relationship_type)
);

COMMENT ON TABLE relationships IS 'All connections between entities with evidence backing';
COMMENT ON COLUMN relationships.strength IS 'Computed strength 0.0-1.5 (>1.0 with evidence multiplier)';
```


---

### Table: investigations

Investigation workspaces that group FIRs, entities, and hypotheses.

```sql
CREATE TABLE investigations (
    investigation_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    primary_fir_id      UUID REFERENCES firs(fir_id),
    status              VARCHAR(30) NOT NULL DEFAULT 'OPEN'
                        CHECK (status IN ('OPEN','ACTIVE','SUSPENDED','CLOSED','MERGED')),
    owner_id            UUID NOT NULL,
    team_ids            UUID[] NOT NULL DEFAULT '{}',
    hypothesis          TEXT,
    priority            VARCHAR(20) NOT NULL DEFAULT 'MEDIUM'
                        CHECK (priority IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    closed_at           TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE investigations IS 'Investigation workspaces - collaborative case management';
COMMENT ON COLUMN investigations.hypothesis IS 'Current working hypothesis maintained by the IO';
```

---

### Table: investigation_evidence

Evidence pinned to an investigation by team members.

```sql
CREATE TABLE investigation_evidence (
    investigation_id    UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    entity_id           UUID REFERENCES entities(entity_id),
    fir_id              UUID REFERENCES firs(fir_id),
    note                TEXT,
    pinned_by           UUID NOT NULL,
    pinned_at           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    tags                TEXT[] NOT NULL DEFAULT '{}',
    relevance_score     REAL DEFAULT 1.0,

    PRIMARY KEY (investigation_id, COALESCE(entity_id, '00000000-0000-0000-0000-000000000000'::UUID), COALESCE(fir_id, '00000000-0000-0000-0000-000000000000'::UUID)),
    CONSTRAINT chk_evidence_target CHECK (entity_id IS NOT NULL OR fir_id IS NOT NULL)
);

COMMENT ON TABLE investigation_evidence IS 'Evidence items pinned to investigations by team members';
```

---

### Table: investigation_timeline

Timeline events reconstructed for an investigation.

```sql
CREATE TABLE investigation_timeline (
    timeline_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id    UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    event_time          TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type          VARCHAR(50) NOT NULL
                        CHECK (event_type IN (
                            'CRIME_OCCURRED','FIR_FILED','ARREST','BAIL',
                            'EVIDENCE_COLLECTED','WITNESS_STATEMENT','CHARGESHEET',
                            'COURT_HEARING','SIGHTING','COMMUNICATION','TRANSACTION',
                            'CUSTOM'
                        )),
    description         TEXT NOT NULL,
    source_fir_id       UUID REFERENCES firs(fir_id),
    source_entity_id    UUID REFERENCES entities(entity_id),
    confidence          REAL NOT NULL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    created_by          UUID NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE investigation_timeline IS 'Chronological event reconstruction for investigations';
```


---

### Table: intelligence_cards

Cards are materialized outputs of deterministic engines (not agent state); each card should reference an engine run and provenance records.

Pre-computed intelligence objects cached for fast retrieval.

```sql
CREATE TABLE intelligence_cards (
    card_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_type           VARCHAR(50) NOT NULL
                        CHECK (card_type IN (
                            'NETWORK_INTELLIGENCE','OFFENDER_PROFILE',
                            'HOTSPOT','FINANCIAL_TRAIL','SIMILAR_CASE'
                        )),
    subject_entity_id   UUID REFERENCES entities(entity_id),
    subject_fir_id      UUID REFERENCES firs(fir_id),
    data                JSONB NOT NULL,
    generated_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    valid_until         TIMESTAMP WITH TIME ZONE NOT NULL,
    version             INT NOT NULL DEFAULT 1,
    generated_by        VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
    superseded_by       UUID REFERENCES intelligence_cards(card_id),

    CONSTRAINT chk_card_subject CHECK (subject_entity_id IS NOT NULL OR subject_fir_id IS NOT NULL)
);

COMMENT ON TABLE intelligence_cards IS 'Materialized intelligence objects - cached ontology computations';
COMMENT ON COLUMN intelligence_cards.valid_until IS 'Card must be recomputed after this timestamp';
```

---

### Table: audit_logs

Immutable audit trail with hash chain for tamper detection.

```sql
CREATE TABLE audit_logs (
    log_id              BIGSERIAL PRIMARY KEY,
    timestamp           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id             UUID NOT NULL,
    user_role           VARCHAR(30) NOT NULL,
    action              VARCHAR(50) NOT NULL
                        CHECK (action IN (
                            'SEARCH','VIEW','CREATE','UPDATE','DELETE',
                            'EXPORT','SHARE','ESCALATE','VERIFY','LOGIN',
                            'LOGOUT','QUERY_ONTOLOGY','GENERATE_CARD',
                            'CREATE_INVESTIGATION','ADD_EVIDENCE','LINK_CASES'
                        )),
    resource_type       VARCHAR(50) NOT NULL,
    resource_id         VARCHAR(255) NOT NULL,
    details             JSONB DEFAULT '{}',
    ip_address          INET,
    session_id          UUID,
    hash_chain          VARCHAR(128) NOT NULL,
    prev_hash           VARCHAR(128)
);

COMMENT ON TABLE audit_logs IS 'Immutable audit trail - every system interaction logged';
COMMENT ON COLUMN audit_logs.hash_chain IS 'SHA-512: hash(prev_hash + timestamp + user_id + action + resource_id)';
COMMENT ON COLUMN audit_logs.prev_hash IS 'Hash of previous log entry for tamper detection chain';

-- Trigger for hash chain computation
CREATE OR REPLACE FUNCTION compute_audit_hash() RETURNS TRIGGER AS $$
DECLARE
    prev_record audit_logs%ROWTYPE;
BEGIN
    SELECT * INTO prev_record FROM audit_logs ORDER BY log_id DESC LIMIT 1;
    
    IF prev_record IS NULL THEN
        NEW.prev_hash := 'GENESIS';
    ELSE
        NEW.prev_hash := prev_record.hash_chain;
    END IF;
    
    NEW.hash_chain := encode(
        digest(
            COALESCE(NEW.prev_hash, '') || 
            NEW.timestamp::TEXT || 
            NEW.user_id::TEXT || 
            NEW.action || 
            NEW.resource_id,
            'sha512'
        ),
        'hex'
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_hash
    BEFORE INSERT ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION compute_audit_hash();
```


---

### Indexes

```sql
-- =============================================================================
-- FIRs Indexes
-- =============================================================================

-- GIN index on IPC sections array for containment queries (@> operator)
CREATE INDEX idx_firs_ipc_sections ON firs USING GIN (ipc_sections);

-- HNSW index on narrative vector for approximate nearest neighbor search
CREATE INDEX idx_firs_narrative_vec ON firs USING hnsw (narrative_vec vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- B-tree on crime_date for range queries
CREATE INDEX idx_firs_crime_date ON firs (crime_date DESC);

-- Composite index on jurisdiction
CREATE INDEX idx_firs_ps_district ON firs (ps_code, district);

-- Full-text search GIN indexes on narratives
CREATE INDEX idx_firs_narrative_en_fts ON firs USING GIN (to_tsvector('english', narrative_en));
CREATE INDEX idx_firs_narrative_kn_fts ON firs USING GIN (to_tsvector('simple', narrative_kn));

-- Status + priority for filtered queries
CREATE INDEX idx_firs_status_priority ON firs (status, priority);

-- Crime category for analytics
CREATE INDEX idx_firs_category ON firs (crime_category, crime_subtype);

-- IO officer for "my cases" queries
CREATE INDEX idx_firs_io_officer ON firs (io_officer_id) WHERE io_officer_id IS NOT NULL;

-- =============================================================================
-- Entities Indexes
-- =============================================================================

-- GIN on attributes JSONB for flexible attribute queries
CREATE INDEX idx_entities_attributes ON entities USING GIN (attributes);

-- B-tree on entity_type + canonical_value for resolution lookups
CREATE INDEX idx_entities_type_canonical ON entities (entity_type, canonical_value);

-- Trigram index for fuzzy name matching
CREATE INDEX idx_entities_value_trgm ON entities USING GIN (entity_value gin_trgm_ops);

-- Risk score for high-risk entity queries
CREATE INDEX idx_entities_risk ON entities (risk_score DESC) WHERE risk_score > 0.5;

-- Last seen for recency queries
CREATE INDEX idx_entities_last_seen ON entities (last_seen DESC);

-- Exclude merged entities from normal queries
CREATE INDEX idx_entities_active ON entities (entity_type, entity_id) WHERE merged_into IS NULL;

-- =============================================================================
-- FIR-Entities Indexes
-- =============================================================================

-- Reverse lookup: find all FIRs for an entity
CREATE INDEX idx_fir_entities_entity ON fir_entities (entity_id, role);

-- Confidence filter
CREATE INDEX idx_fir_entities_confidence ON fir_entities (confidence DESC) WHERE confidence < 1.0;

-- =============================================================================
-- Relationships Indexes
-- =============================================================================

-- Find all relationships for an entity (both directions)
CREATE INDEX idx_relationships_source ON relationships (source_entity_id, relationship_type);
CREATE INDEX idx_relationships_target ON relationships (target_entity_id, relationship_type);

-- Strength-based filtering
CREATE INDEX idx_relationships_strength ON relationships (strength DESC) WHERE strength > 0.5;

-- Unverified relationships for review queue
CREATE INDEX idx_relationships_unverified ON relationships (discovered_at DESC) WHERE verified = FALSE;

-- Discovery method for audit
CREATE INDEX idx_relationships_discovery ON relationships (discovery_method, discovered_at DESC);

-- =============================================================================
-- Investigations Indexes
-- =============================================================================

-- Owner's investigations
CREATE INDEX idx_investigations_owner ON investigations (owner_id, status);

-- Team member lookup (GIN for array contains)
CREATE INDEX idx_investigations_team ON investigations USING GIN (team_ids);

-- Status filter
CREATE INDEX idx_investigations_status ON investigations (status, updated_at DESC);

-- =============================================================================
-- Investigation Timeline Indexes
-- =============================================================================

-- Timeline ordered by event time within investigation
CREATE INDEX idx_timeline_investigation ON investigation_timeline (investigation_id, event_time);

-- Event type filter
CREATE INDEX idx_timeline_event_type ON investigation_timeline (event_type, event_time DESC);

-- =============================================================================
-- Intelligence Cards Indexes
-- =============================================================================

-- Card type + subject for lookup
CREATE INDEX idx_cards_type_entity ON intelligence_cards (card_type, subject_entity_id)
    WHERE subject_entity_id IS NOT NULL;
CREATE INDEX idx_cards_type_fir ON intelligence_cards (card_type, subject_fir_id)
    WHERE subject_fir_id IS NOT NULL;

-- Valid cards only (not expired, not superseded)
CREATE INDEX idx_cards_valid ON intelligence_cards (card_type, valid_until DESC)
    WHERE superseded_by IS NULL AND valid_until > NOW();

-- GIN on card data for JSONB queries
CREATE INDEX idx_cards_data ON intelligence_cards USING GIN (data);

-- =============================================================================
-- Audit Logs Indexes
-- =============================================================================

-- User activity lookup
CREATE INDEX idx_audit_user ON audit_logs (user_id, timestamp DESC);

-- Resource access history
CREATE INDEX idx_audit_resource ON audit_logs (resource_type, resource_id, timestamp DESC);

-- Action type for analytics
CREATE INDEX idx_audit_action ON audit_logs (action, timestamp DESC);

-- Hash chain verification
CREATE INDEX idx_audit_hash ON audit_logs (hash_chain);

-- Time-based partitioning support
CREATE INDEX idx_audit_timestamp ON audit_logs (timestamp DESC);
```


---

## Neo4j — AppSail Graph Store

### Node Labels and Properties

```cypher
// =============================================================================
// NODE DEFINITIONS
// =============================================================================

// FIR Node
CREATE (f:FIR {
    fir_id: 'uuid',
    fir_number: 'PS001/2026/0142',
    ps_code: 'BNG-001',
    district: 'Bengaluru Urban',
    crime_date: datetime('2026-07-20T14:30:00+05:30'),
    ipc_sections: [302, 120],
    crime_category: 'murder',
    crime_subtype: 'premeditated',
    status: 'UNDER_INVESTIGATION',
    priority: 'CRITICAL',
    mo_keywords: ['knife', 'night', 'residential'],
    created_at: datetime()
});

// Person Node
CREATE (p:Person {
    entity_id: 'uuid',
    name: 'RAMESH KUMAR',
    canonical_value: 'RAMESH KUMAR|1985-03-15|SURESH KUMAR',
    dob: date('1985-03-15'),
    gender: 'MALE',
    father_name: 'SURESH KUMAR',
    district: 'Bengaluru Urban',
    risk_score: 0.78,
    fir_count: 7,
    first_seen: datetime('2020-01-15'),
    last_seen: datetime('2026-07-20')
});

// Vehicle Node
CREATE (v:Vehicle {
    entity_id: 'uuid',
    registration_number: 'KA-01-AB-1234',
    canonical_value: 'KA-01-AB-1234',
    chassis_number: 'MBLHA10EXHP000123',
    make: 'Honda',
    model: 'Activa',
    color: 'Black',
    vehicle_type: 'two-wheeler',
    first_seen: datetime('2024-06-10'),
    last_seen: datetime('2026-07-18')
});

// Phone Node
CREATE (ph:Phone {
    entity_id: 'uuid',
    number: '+919876543210',
    canonical_value: '+919876543210',
    imei: '351234567890123',
    carrier: 'Jio',
    first_seen: datetime('2023-01-01'),
    last_seen: datetime('2026-07-20')
});

// UPI Node
CREATE (u:UPI {
    entity_id: 'uuid',
    upi_id: 'ramesh85@paytm',
    canonical_value: 'ramesh85@paytm',
    linked_phone: '+919876543210',
    provider: 'Paytm',
    first_seen: datetime('2024-03-15'),
    last_seen: datetime('2026-07-19')
});

// BankAccount Node
CREATE (ba:BankAccount {
    entity_id: 'uuid',
    account_number: '9876543210123456',
    canonical_value: 'SBIN0001234:9876543210123456',
    ifsc: 'SBIN0001234',
    bank_name: 'State Bank of India',
    holder_name: 'RAMESH KUMAR',
    account_type: 'SAVINGS',
    first_seen: datetime('2022-06-01'),
    last_seen: datetime('2026-07-20')
});

// CCTV Node
CREATE (c:CCTV {
    entity_id: 'uuid',
    camera_id: 'CAM-BNG-MG-ROAD-042',
    canonical_value: 'CAM-BNG-MG-ROAD-042@LOC-uuid',
    location_lat: 12.9716,
    location_lng: 77.5946,
    owner: 'BBMP',
    type: 'PTZ',
    resolution: '1080p',
    status: 'ACTIVE'
});

// Evidence Node
CREATE (e:Evidence {
    entity_id: 'uuid',
    evidence_type: 'DIGITAL',
    hash: 'sha256:abc123...',
    canonical_value: 'sha256:abc123...',
    file_type: 'video/mp4',
    source: 'CCTV_FOOTAGE',
    collected_at: datetime('2026-07-20T15:00:00+05:30'),
    chain_of_custody: ['IO-001', 'FSL-BNG']
});

// Location Node
CREATE (l:Location {
    entity_id: 'uuid',
    lat: 12.9716,
    lng: 77.5946,
    canonical_value: '12.971600,77.594600',
    address: '42, MG Road, Bengaluru',
    landmark: 'Near Trinity Circle',
    ps_jurisdiction: 'BNG-001',
    district: 'Bengaluru Urban',
    location_type: 'CRIME_SCENE'
});

// PoliceStation Node
CREATE (ps:PoliceStation {
    entity_id: 'uuid',
    ps_code: 'BNG-001',
    canonical_value: 'BNG-001',
    name: 'Cubbon Park Police Station',
    district: 'Bengaluru Urban',
    zone: 'Bengaluru Zone',
    lat: 12.9763,
    lng: 77.5929,
    sho_name: 'Inspector Sharma'
});

// CrimeCategory Node
CREATE (cc:CrimeCategory {
    entity_id: 'uuid',
    category: 'murder',
    subtype: 'premeditated',
    canonical_value: 'murder:premeditated',
    ipc_sections: [302, 120],
    severity_level: 5
});
```

---

### Constraints and Indexes

```cypher
// =============================================================================
// UNIQUE CONSTRAINTS (also creates indexes)
// =============================================================================

CREATE CONSTRAINT constraint_fir_id FOR (f:FIR) REQUIRE f.fir_id IS UNIQUE;
CREATE CONSTRAINT constraint_person_id FOR (p:Person) REQUIRE p.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_vehicle_id FOR (v:Vehicle) REQUIRE v.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_phone_id FOR (ph:Phone) REQUIRE ph.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_upi_id FOR (u:UPI) REQUIRE u.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_bank_id FOR (ba:BankAccount) REQUIRE ba.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_cctv_id FOR (c:CCTV) REQUIRE c.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_evidence_id FOR (e:Evidence) REQUIRE e.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_location_id FOR (l:Location) REQUIRE l.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_ps_id FOR (ps:PoliceStation) REQUIRE ps.entity_id IS UNIQUE;
CREATE CONSTRAINT constraint_category_id FOR (cc:CrimeCategory) REQUIRE cc.entity_id IS UNIQUE;

// =============================================================================
// COMPOSITE INDEXES for entity resolution
// =============================================================================

CREATE INDEX index_person_canonical FOR (p:Person) ON (p.canonical_value);
CREATE INDEX index_vehicle_canonical FOR (v:Vehicle) ON (v.canonical_value);
CREATE INDEX index_phone_canonical FOR (ph:Phone) ON (ph.canonical_value);
CREATE INDEX index_upi_canonical FOR (u:UPI) ON (u.canonical_value);
CREATE INDEX index_bank_canonical FOR (ba:BankAccount) ON (ba.canonical_value);
CREATE INDEX index_location_canonical FOR (l:Location) ON (l.canonical_value);
CREATE INDEX index_cctv_canonical FOR (c:CCTV) ON (c.canonical_value);
CREATE INDEX index_ps_canonical FOR (ps:PoliceStation) ON (ps.canonical_value);
CREATE INDEX index_category_canonical FOR (cc:CrimeCategory) ON (cc.canonical_value);

// =============================================================================
// PROPERTY INDEXES for common queries
// =============================================================================

CREATE INDEX index_fir_ps_code FOR (f:FIR) ON (f.ps_code);
CREATE INDEX index_fir_district FOR (f:FIR) ON (f.district);
CREATE INDEX index_fir_status FOR (f:FIR) ON (f.status);
CREATE INDEX index_fir_crime_date FOR (f:FIR) ON (f.crime_date);
CREATE INDEX index_person_name FOR (p:Person) ON (p.name);
CREATE INDEX index_person_district FOR (p:Person) ON (p.district);
CREATE INDEX index_person_risk FOR (p:Person) ON (p.risk_score);
CREATE INDEX index_vehicle_reg FOR (v:Vehicle) ON (v.registration_number);
CREATE INDEX index_phone_number FOR (ph:Phone) ON (ph.number);

// Full-text index for narrative search within Neo4j
CREATE FULLTEXT INDEX fir_narrative FOR (f:FIR) ON EACH [f.fir_number, f.crime_category, f.crime_subtype];
CREATE FULLTEXT INDEX person_search FOR (p:Person) ON EACH [p.name, p.father_name];
```


---

### Relationship Types with Properties

```cypher
// =============================================================================
// DIRECT RELATIONSHIPS (extracted from data)
// =============================================================================

// Person accused in FIR
CREATE (p:Person)-[:ACCUSED_IN {
    strength: 1.0,
    fir_count: 1,
    confidence: 0.95,
    extraction_method: 'NER',
    first_seen: datetime(),
    last_seen: datetime()
}]->(f:FIR);

// Person is victim in FIR
CREATE (p:Person)-[:VICTIM_IN {
    strength: 1.0,
    fir_count: 1,
    confidence: 0.98,
    extraction_method: 'NER',
    first_seen: datetime(),
    last_seen: datetime()
}]->(f:FIR);

// Person is witness in FIR
CREATE (p:Person)-[:WITNESS_IN {
    strength: 0.8,
    fir_count: 1,
    confidence: 0.90,
    extraction_method: 'NER',
    first_seen: datetime(),
    last_seen: datetime()
}]->(f:FIR);

// Person owns phone
CREATE (p:Person)-[:OWNS_PHONE {
    strength: 0.9,
    fir_count: 1,
    verified: true,
    source: 'TELECOM_RECORDS',
    first_seen: datetime(),
    last_seen: datetime()
}]->(ph:Phone);

// Person owns vehicle
CREATE (p:Person)-[:OWNS_VEHICLE {
    strength: 0.9,
    fir_count: 1,
    verified: true,
    source: 'RTO_RECORDS',
    first_seen: datetime(),
    last_seen: datetime()
}]->(v:Vehicle);

// Person owns bank account
CREATE (p:Person)-[:OWNS_ACCOUNT {
    strength: 0.9,
    fir_count: 1,
    verified: true,
    source: 'BANK_RECORDS',
    first_seen: datetime(),
    last_seen: datetime()
}]->(ba:BankAccount);

// FIR located at location
CREATE (f:FIR)-[:LOCATED_AT {
    strength: 1.0,
    location_type: 'CRIME_SCENE',
    geocoded: true,
    first_seen: datetime(),
    last_seen: datetime()
}]->(l:Location);

// Person captured by CCTV
CREATE (p:Person)-[:CAPTURED_BY {
    strength: 0.7,
    fir_count: 1,
    confidence: 0.75,
    timestamp: datetime(),
    method: 'FACE_RECOGNITION',
    first_seen: datetime(),
    last_seen: datetime()
}]->(c:CCTV);

// Phone called phone (CDR)
CREATE (ph1:Phone)-[:CALLED {
    strength: 0.6,
    call_count: 15,
    total_duration_seconds: 3420,
    first_call: datetime(),
    last_call: datetime(),
    fir_count: 2,
    first_seen: datetime(),
    last_seen: datetime()
}]->(ph2:Phone);

// Bank account transacted with bank account
CREATE (ba1:BankAccount)-[:TRANSACTED_WITH {
    strength: 0.8,
    txn_count: 8,
    total_amount: 250000,
    avg_amount: 31250,
    first_txn: datetime(),
    last_txn: datetime(),
    methods: ['UPI', 'NEFT'],
    fir_count: 1,
    first_seen: datetime(),
    last_seen: datetime()
}]->(ba2:BankAccount);

// Person belongs to gang/organization
CREATE (p:Person)-[:BELONGS_TO_GANG {
    strength: 0.9,
    role: 'MEMBER',
    fir_count: 3,
    intelligence_source: 'PATTERN_ANALYSIS',
    first_seen: datetime(),
    last_seen: datetime()
}]->(o:Organization);

// FIR under jurisdiction of police station
CREATE (f:FIR)-[:JURISDICTION_OF {
    strength: 1.0,
    first_seen: datetime(),
    last_seen: datetime()
}]->(ps:PoliceStation);

// FIR categorized as crime category
CREATE (f:FIR)-[:CATEGORIZED_AS {
    strength: 1.0,
    primary: true,
    first_seen: datetime(),
    last_seen: datetime()
}]->(cc:CrimeCategory);

// =============================================================================
// COMPUTED RELATIONSHIPS (derived by algorithms)
// =============================================================================

// Co-accused: two persons accused in the same FIR(s)
CREATE (p1:Person)-[:CO_ACCUSED_WITH {
    strength: 0.85,
    shared_fir_count: 3,
    shared_fir_ids: ['uuid1', 'uuid2', 'uuid3'],
    discovery_method: 'COMPUTED',
    computed_at: datetime(),
    fir_count: 3,
    first_seen: datetime(),
    last_seen: datetime()
}]->(p2:Person);

// Shares phone: two persons linked to the same phone number
CREATE (p1:Person)-[:SHARES_PHONE_WITH {
    strength: 0.85,
    shared_phone_id: 'uuid',
    shared_phone_number: '+919876543210',
    discovery_method: 'COMPUTED',
    computed_at: datetime(),
    fir_count: 2,
    first_seen: datetime(),
    last_seen: datetime()
}]->(p2:Person);

// Shares vehicle: two persons linked to the same vehicle
CREATE (p1:Person)-[:SHARES_VEHICLE_WITH {
    strength: 0.80,
    shared_vehicle_id: 'uuid',
    shared_registration: 'KA-01-AB-1234',
    discovery_method: 'COMPUTED',
    computed_at: datetime(),
    fir_count: 1,
    first_seen: datetime(),
    last_seen: datetime()
}]->(p2:Person);

// Shares UPI: two persons linked to the same UPI ID
CREATE (p1:Person)-[:SHARES_UPI_WITH {
    strength: 0.85,
    shared_upi_id: 'uuid',
    shared_upi_value: 'shared@paytm',
    discovery_method: 'COMPUTED',
    computed_at: datetime(),
    fir_count: 1,
    first_seen: datetime(),
    last_seen: datetime()
}]->(p2:Person);

// Financial flow: money trail between persons (through accounts)
CREATE (p1:Person)-[:FINANCIAL_FLOW {
    strength: 0.75,
    total_amount: 500000,
    hop_count: 3,
    layering_pattern: 'FAN_OUT',
    trail_id: 'uuid',
    discovery_method: 'FINANCIAL_ANALYSIS',
    computed_at: datetime(),
    fir_count: 1,
    first_seen: datetime(),
    last_seen: datetime()
}]->(p2:Person);

// Temporal proximity: FIRs close in time and space
CREATE (f1:FIR)-[:TEMPORAL_PROXIMITY {
    strength: 0.72,
    time_diff_hours: 4.5,
    distance_km: 1.2,
    shared_entity_count: 0,
    discovery_method: 'COMPUTED',
    computed_at: datetime(),
    fir_count: 2,
    first_seen: datetime(),
    last_seen: datetime()
}]->(f2:FIR);

// Same modus operandi: FIRs with similar crime methods
CREATE (f1:FIR)-[:SAME_MODUS_OPERANDI {
    strength: 0.88,
    cosine_similarity: 0.88,
    shared_mo_keywords: ['knife', 'night', 'gold-chain'],
    discovery_method: 'PATTERN_MATCH',
    computed_at: datetime(),
    fir_count: 2,
    first_seen: datetime(),
    last_seen: datetime()
}]->(f2:FIR);
```

---

### Graph Data Science (GDS) Projections

```cypher
// =============================================================================
// GDS GRAPH PROJECTIONS
// =============================================================================

// 1. Co-Offender Network Graph
// Used for: community detection, centrality analysis, gang identification
CALL gds.graph.project(
    'co-offender-graph',
    {
        Person: {
            properties: ['risk_score', 'fir_count']
        }
    },
    {
        CO_ACCUSED_WITH: {
            type: 'CO_ACCUSED_WITH',
            orientation: 'UNDIRECTED',
            properties: ['strength', 'shared_fir_count']
        },
        SHARES_PHONE_WITH: {
            type: 'SHARES_PHONE_WITH',
            orientation: 'UNDIRECTED',
            properties: ['strength']
        },
        SHARES_VEHICLE_WITH: {
            type: 'SHARES_VEHICLE_WITH',
            orientation: 'UNDIRECTED',
            properties: ['strength']
        },
        SHARES_UPI_WITH: {
            type: 'SHARES_UPI_WITH',
            orientation: 'UNDIRECTED',
            properties: ['strength']
        }
    }
);

// Algorithms on co-offender-graph:
// - gds.louvain (community detection → gang identification)
// - gds.betweennessCentrality (bridge identification)
// - gds.pageRank (influence scoring)
// - gds.triangleCount (group cohesion)

// 2. Financial Flow Graph
// Used for: money laundering detection, mule account identification
CALL gds.graph.project(
    'financial-flow-graph',
    {
        Person: { properties: ['risk_score'] },
        BankAccount: { properties: [] },
        UPI: { properties: [] }
    },
    {
        TRANSACTED_WITH: {
            type: 'TRANSACTED_WITH',
            orientation: 'NATURAL',
            properties: ['total_amount', 'txn_count', 'strength']
        },
        OWNS_ACCOUNT: {
            type: 'OWNS_ACCOUNT',
            orientation: 'NATURAL',
            properties: ['strength']
        },
        FINANCIAL_FLOW: {
            type: 'FINANCIAL_FLOW',
            orientation: 'NATURAL',
            properties: ['total_amount', 'hop_count', 'strength']
        }
    }
);

// Algorithms on financial-flow-graph:
// - gds.allShortestPaths (trace money movement)
// - gds.degree (identify mule accounts with high in-degree)
// - gds.weaklyConnectedComponents (find financial clusters)
// - Custom: fan-out detection (single source → many destinations)

// 3. Entity Similarity Graph
// Used for: case linking, pattern detection, similar offender identification
CALL gds.graph.project(
    'entity-similarity-graph',
    {
        FIR: { properties: ['crime_date'] },
        Person: { properties: ['risk_score'] }
    },
    {
        SAME_MODUS_OPERANDI: {
            type: 'SAME_MODUS_OPERANDI',
            orientation: 'UNDIRECTED',
            properties: ['strength', 'cosine_similarity']
        },
        TEMPORAL_PROXIMITY: {
            type: 'TEMPORAL_PROXIMITY',
            orientation: 'UNDIRECTED',
            properties: ['strength', 'time_diff_hours']
        },
        ACCUSED_IN: {
            type: 'ACCUSED_IN',
            orientation: 'NATURAL',
            properties: ['strength']
        }
    }
);

// Algorithms on entity-similarity-graph:
// - gds.nodeSimilarity (find similar FIRs based on shared entities)
// - gds.knn (k-nearest neighbor FIRs)
// - gds.weaklyConnectedComponents (case clusters)
// - Custom: serial offender detection (Person → multiple similar FIRs)
```

---

### Cypher Queries for Computed Relationships

```cypher
// =============================================================================
// BATCH COMPUTATION QUERIES (run periodically)
// =============================================================================

// Compute CO_ACCUSED_WITH relationships
MATCH (p1:Person)-[:ACCUSED_IN]->(f:FIR)<-[:ACCUSED_IN]-(p2:Person)
WHERE p1.entity_id < p2.entity_id  // avoid duplicates
WITH p1, p2, COLLECT(f.fir_id) AS shared_firs, COUNT(f) AS shared_count
WHERE shared_count >= 1
MERGE (p1)-[r:CO_ACCUSED_WITH]->(p2)
SET r.strength = toFloat(shared_count) / 
    toFloat(SIZE([(p1)-[:ACCUSED_IN]->() | 1]) + SIZE([(p2)-[:ACCUSED_IN]->() | 1]) - shared_count),
    r.shared_fir_count = shared_count,
    r.shared_fir_ids = shared_firs,
    r.discovery_method = 'COMPUTED',
    r.computed_at = datetime(),
    r.last_seen = datetime();

// Compute SHARES_PHONE_WITH relationships
MATCH (p1:Person)-[:OWNS_PHONE]->(ph:Phone)<-[:OWNS_PHONE]-(p2:Person)
WHERE p1.entity_id < p2.entity_id
WITH p1, p2, ph
MERGE (p1)-[r:SHARES_PHONE_WITH]->(p2)
SET r.strength = 0.85,
    r.shared_phone_id = ph.entity_id,
    r.shared_phone_number = ph.number,
    r.discovery_method = 'COMPUTED',
    r.computed_at = datetime(),
    r.last_seen = datetime();

// Compute SHARES_VEHICLE_WITH relationships
MATCH (p1:Person)-[:OWNS_VEHICLE]->(v:Vehicle)<-[:OWNS_VEHICLE]-(p2:Person)
WHERE p1.entity_id < p2.entity_id
WITH p1, p2, v
MERGE (p1)-[r:SHARES_VEHICLE_WITH]->(p2)
SET r.strength = 0.80,
    r.shared_vehicle_id = v.entity_id,
    r.shared_registration = v.registration_number,
    r.discovery_method = 'COMPUTED',
    r.computed_at = datetime(),
    r.last_seen = datetime();

// Compute SHARES_UPI_WITH relationships
MATCH (p1:Person)-[:OWNS_ACCOUNT]->(:BankAccount)<-[:LINKED_TO]-(u:UPI)-[:LINKED_TO]->(:BankAccount)<-[:OWNS_ACCOUNT]-(p2:Person)
WHERE p1.entity_id < p2.entity_id
WITH p1, p2, u
MERGE (p1)-[r:SHARES_UPI_WITH]->(p2)
SET r.strength = 0.85,
    r.shared_upi_id = u.entity_id,
    r.shared_upi_value = u.upi_id,
    r.discovery_method = 'COMPUTED',
    r.computed_at = datetime(),
    r.last_seen = datetime();

// Compute TEMPORAL_PROXIMITY between FIRs
MATCH (f1:FIR)-[:LOCATED_AT]->(l1:Location), (f2:FIR)-[:LOCATED_AT]->(l2:Location)
WHERE f1.fir_id < f2.fir_id
  AND f1.district = f2.district
  AND abs(duration.between(f1.crime_date, f2.crime_date).hours) <= 72
  AND point.distance(point({latitude: l1.lat, longitude: l1.lng}), point({latitude: l2.lat, longitude: l2.lng})) < 5000
WITH f1, f2,
     abs(duration.between(f1.crime_date, f2.crime_date).hours) AS hours_diff,
     point.distance(point({latitude: l1.lat, longitude: l1.lng}), point({latitude: l2.lat, longitude: l2.lng})) / 1000.0 AS dist_km
MERGE (f1)-[r:TEMPORAL_PROXIMITY]->(f2)
SET r.strength = 1.0 - (toFloat(hours_diff) / 72.0),
    r.time_diff_hours = hours_diff,
    r.distance_km = dist_km,
    r.discovery_method = 'COMPUTED',
    r.computed_at = datetime(),
    r.last_seen = datetime();
```

---

## Data Synchronization (Catalyst Signals → Functions → deterministic engines → projections)

Catalyst Data Store remains authoritative for structured records and pgvector HNSW embeddings. Catalyst Signals emits data-change events; Catalyst Functions consume those events and update the Neo4j graph projection, embedding records, and precomputed intelligence cards.

```text
Catalyst Data Store
       │ Catalyst Signals
       ▼
Catalyst Functions
   ├──► Neo4j 5 Community on AppSail (graph projection)
   ├──► pgvector HNSW embedding records in Catalyst Data Store
   ├──► Stratus (precomputed JSONs, reports, exports)
   └──► Catalyst Cache (hot cards and session state)
```

### Sync rules
1. Writes and authoritative reads use Catalyst Data Store.
2. Catalyst Signals delivers change events to Functions; delivery and projection lag require measurement.
3. Functions update Neo4j and precomputed artifacts idempotently.
4. Intelligence cards are durable/precomputed in Stratus or Data Store as appropriate; hot copies may be held in Catalyst Cache.
5. Raw PostgreSQL extensions, triggers, and DDL in this document remain a local/logical reference until Catalyst compatibility is validated.


---

*Schema version: 1.0 | Last updated: 2026-07-23*
