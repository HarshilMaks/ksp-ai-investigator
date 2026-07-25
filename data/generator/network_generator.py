"""Deterministic ontology links for synthetic FIR fixtures."""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from src.domain.enums import EntityType, ExtractionMethod, FIREntityRole, RelationshipType
from src.domain.models import Entity, FIR, FIREntityLink, Relationship
from src.domain.ontology import canonicalize

from .entity_generator import generate_entities
from .karnataka_context import STATIONS


def _id(seed: int, kind: str, index: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"ksp-investigateai:synthetic:{seed}:{kind}:{index}")


def generate_network_records(
    firs: list[FIR],
    *,
    seed: int = 20260725,
) -> tuple[list[Entity], list[FIREntityLink], list[Relationship]]:
    """Create evidence-backed links for each synthetic FIR."""

    generated = generate_entities(len(firs), seed=seed, observed_at=firs[0].registration_date if firs else None)
    entities = list(generated)
    links: list[FIREntityLink] = []
    relationships: list[Relationship] = []
    stations_by_code = {station.ps_code: station for station in STATIONS}
    station_entity_ids: dict[str, UUID] = {}
    category_entity_ids: dict[str, UUID] = {}

    for index, fir in enumerate(firs, start=1):
        person, phone, vehicle, upi = generated[(index - 1) * 4 : index * 4]
        fir_entity = Entity(
            entity_id=_id(seed, "fir-entity", str(index)),
            entity_type=EntityType.FIR,
            entity_value=fir.fir_number,
            canonical_value=canonicalize(EntityType.FIR, fir.fir_number),
            attributes={"synthetic": True},
            first_seen=fir.registration_date,
            last_seen=fir.registration_date,
            created_at=fir.registration_date,
        )
        entities.append(fir_entity)
        links.extend(
            [
                FIREntityLink(fir.fir_id, person.entity_id, FIREntityRole.ACCUSED, extraction_method=ExtractionMethod.MANUAL, extracted_at=fir.registration_date),
                FIREntityLink(fir.fir_id, phone.entity_id, FIREntityRole.MENTIONED, extraction_method=ExtractionMethod.REGEX, extracted_at=fir.registration_date),
                FIREntityLink(fir.fir_id, vehicle.entity_id, FIREntityRole.VEHICLE_USED, extraction_method=ExtractionMethod.LOOKUP, extracted_at=fir.registration_date),
                FIREntityLink(fir.fir_id, upi.entity_id, FIREntityRole.MENTIONED, extraction_method=ExtractionMethod.LOOKUP, extracted_at=fir.registration_date),
            ]
        )
        relationships.extend(
            [
                Relationship(person.entity_id, fir_entity.entity_id, RelationshipType.ACCUSED_IN, relationship_id=_id(seed, "relationship", f"{index}:accused"), evidence_fir_ids=(fir.fir_id,), discovered_at=fir.registration_date),
                Relationship(person.entity_id, phone.entity_id, RelationshipType.OWNS_PHONE, relationship_id=_id(seed, "relationship", f"{index}:phone"), strength=0.9, evidence_fir_ids=(fir.fir_id,), discovered_at=fir.registration_date),
                Relationship(person.entity_id, vehicle.entity_id, RelationshipType.OWNS_VEHICLE, relationship_id=_id(seed, "relationship", f"{index}:vehicle"), strength=0.9, evidence_fir_ids=(fir.fir_id,), discovered_at=fir.registration_date),
            ]
        )

        station = stations_by_code[fir.ps_code]
        station_id = station_entity_ids.setdefault(station.ps_code, _id(seed, "station", station.ps_code))
        if not any(entity.entity_id == station_id for entity in entities):
            entities.append(
                Entity(
                    entity_id=station_id,
                    entity_type=EntityType.POLICE_STATION,
                    entity_value=station.name,
                    canonical_value=canonicalize(EntityType.POLICE_STATION, station.ps_code),
                    attributes={"ps_code": station.ps_code, "district": station.district, "synthetic": True},
                    first_seen=fir.registration_date,
                    last_seen=fir.registration_date,
                    created_at=fir.registration_date,
                )
            )
        relationships.append(
            Relationship(fir_entity.entity_id, station_id, RelationshipType.JURISDICTION_OF, evidence_fir_ids=(fir.fir_id,), discovered_at=fir.registration_date)
        )

        category_id = category_entity_ids.setdefault(fir.crime_category, _id(seed, "category", fir.crime_category))
        if not any(entity.entity_id == category_id for entity in entities):
            entities.append(
                Entity(
                    entity_id=category_id,
                    entity_type=EntityType.CRIME_CATEGORY,
                    entity_value=fir.crime_category,
                    canonical_value=canonicalize(EntityType.CRIME_CATEGORY, fir.crime_category),
                    attributes={"ipc_sections": list(fir.ipc_sections), "synthetic": True},
                    first_seen=fir.registration_date,
                    last_seen=fir.registration_date,
                    created_at=fir.registration_date,
                )
            )
        relationships.append(
            Relationship(fir_entity.entity_id, category_id, RelationshipType.CATEGORIZED_AS, evidence_fir_ids=(fir.fir_id,), discovered_at=fir.registration_date)
        )

    return entities, links, relationships
