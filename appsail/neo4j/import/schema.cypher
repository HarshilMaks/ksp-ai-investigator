// Neo4j 5 Community projection schema. Re-running this file is safe.
// DigitalEvidence is the logical Catalyst entity; Evidence is its graph label at the projection boundary.

// Locked relationship vocabulary projected as typed Neo4j relationship types:
// ACCUSED_IN, VICTIM_IN, WITNESS_IN, OWNS_PHONE, OWNS_VEHICLE, OWNS_ACCOUNT,
// LOCATED_AT, CAPTURED_BY, CALLED, TRANSACTED_WITH, CO_ACCUSED_WITH,
// SHARES_PHONE_WITH, SHARES_VEHICLE_WITH, SHARES_UPI_WITH, FINANCIAL_FLOW,
// TEMPORAL_PROXIMITY, SAME_MODUS_OPERANDI, BELONGS_TO_GANG, JURISDICTION_OF,
// CATEGORIZED_AS.

CREATE CONSTRAINT fir_id_unique IF NOT EXISTS FOR (n:FIR) REQUIRE n.fir_id IS UNIQUE;
CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT phone_id_unique IF NOT EXISTS FOR (n:Phone) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT vehicle_id_unique IF NOT EXISTS FOR (n:Vehicle) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT upi_id_unique IF NOT EXISTS FOR (n:UPI) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT bank_account_id_unique IF NOT EXISTS FOR (n:BankAccount) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (n:Location) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT cctv_id_unique IF NOT EXISTS FOR (n:CCTV) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT weapon_id_unique IF NOT EXISTS FOR (n:Weapon) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT organization_id_unique IF NOT EXISTS FOR (n:Organization) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (n:Document) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT digital_evidence_id_unique IF NOT EXISTS FOR (n:DigitalEvidence) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT graph_evidence_id_unique IF NOT EXISTS FOR (n:Evidence) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT address_id_unique IF NOT EXISTS FOR (n:Address) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT entity_fir_id_unique IF NOT EXISTS FOR (n:FIR) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT police_station_id_unique IF NOT EXISTS FOR (n:PoliceStation) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT crime_category_id_unique IF NOT EXISTS FOR (n:CrimeCategory) REQUIRE n.entity_id IS UNIQUE;

CREATE INDEX fir_number_index IF NOT EXISTS FOR (n:FIR) ON (n.fir_number);
CREATE INDEX fir_ps_code_index IF NOT EXISTS FOR (n:FIR) ON (n.ps_code);
CREATE INDEX entity_canonical_value_index IF NOT EXISTS FOR (n:Person) ON (n.canonical_value);
CREATE INDEX entity_type_index IF NOT EXISTS FOR (n:Entity) ON (n.entity_type);
CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:ACCUSED_IN]-() ON (r.relationship_type);
CREATE INDEX relationship_evidence_index IF NOT EXISTS FOR ()-[r:ACCUSED_IN]-() ON (r.evidence_fir_ids);
