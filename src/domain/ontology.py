"""Ontology vocabulary and canonicalization helpers.

This module only normalizes values and exposes governed vocabulary metadata. It does
not resolve people or merge entities; officer-approved resolution is later scope.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .enums import EntityType, RelationshipType, SCHEMA_EXTENSION_ENTITY_TYPES


ENTITY_CANONICAL_RULES = {
    EntityType.PERSON: "UPPERCASE_NAME + DOB + FATHER_NAME",
    EntityType.PHONE: "+91XXXXXXXXXX (E.164)",
    EntityType.VEHICLE: "KA-XX-XX-XXXX normalized plate",
    EntityType.UPI: "lowercase@provider",
    EntityType.BANK_ACCOUNT: "IFSC:ACCOUNT_NUMBER",
    EntityType.LOCATION: "lat,lng at 6 decimal precision",
    EntityType.CCTV: "CAMERA_ID@LOCATION_ID",
    EntityType.WEAPON: "TYPE:MAKE:SERIAL",
    EntityType.ORGANIZATION: "UPPERCASE_NAME + DISTRICT",
    EntityType.DOCUMENT: "DOC_TYPE:DOC_NUMBER",
    EntityType.DIGITAL_EVIDENCE: "SHA256_HASH",
    EntityType.ADDRESS: "NORMALIZED_ADDR + PIN",
    EntityType.FIR: "PS_CODE/YEAR/FIR_NUMBER",
    EntityType.POLICE_STATION: "PS_CODE",
    EntityType.CRIME_CATEGORY: "CATEGORY:SUBTYPE",
}

RELATIONSHIP_ENDPOINTS: dict[RelationshipType, tuple[set[EntityType], set[EntityType]]] = {
    RelationshipType.ACCUSED_IN: ({EntityType.PERSON}, {EntityType.FIR}),
    RelationshipType.VICTIM_IN: ({EntityType.PERSON}, {EntityType.FIR}),
    RelationshipType.WITNESS_IN: ({EntityType.PERSON}, {EntityType.FIR}),
    RelationshipType.OWNS_PHONE: ({EntityType.PERSON}, {EntityType.PHONE}),
    RelationshipType.OWNS_VEHICLE: ({EntityType.PERSON}, {EntityType.VEHICLE}),
    RelationshipType.OWNS_ACCOUNT: ({EntityType.PERSON}, {EntityType.BANK_ACCOUNT}),
    RelationshipType.LOCATED_AT: ({EntityType.FIR}, {EntityType.LOCATION}),
    RelationshipType.CAPTURED_BY: ({EntityType.PERSON}, {EntityType.CCTV}),
    RelationshipType.CALLED: ({EntityType.PHONE}, {EntityType.PHONE}),
    RelationshipType.TRANSACTED_WITH: ({EntityType.BANK_ACCOUNT}, {EntityType.BANK_ACCOUNT}),
    RelationshipType.CO_ACCUSED_WITH: ({EntityType.PERSON}, {EntityType.PERSON}),
    RelationshipType.SHARES_PHONE_WITH: ({EntityType.PERSON}, {EntityType.PERSON}),
    RelationshipType.SHARES_VEHICLE_WITH: ({EntityType.PERSON}, {EntityType.PERSON}),
    RelationshipType.SHARES_UPI_WITH: ({EntityType.PERSON}, {EntityType.PERSON}),
    RelationshipType.FINANCIAL_FLOW: ({EntityType.PERSON}, {EntityType.PERSON}),
    RelationshipType.TEMPORAL_PROXIMITY: ({EntityType.FIR}, {EntityType.FIR}),
    RelationshipType.SAME_MODUS_OPERANDI: ({EntityType.FIR}, {EntityType.FIR}),
    RelationshipType.BELONGS_TO_GANG: ({EntityType.PERSON}, {EntityType.ORGANIZATION}),
    RelationshipType.JURISDICTION_OF: ({EntityType.FIR}, {EntityType.POLICE_STATION}),
    RelationshipType.CATEGORIZED_AS: ({EntityType.FIR}, {EntityType.CRIME_CATEGORY}),
}


def canonicalize(entity_type: EntityType, value: str, *, attributes: dict[str, str] | None = None) -> str:
    """Apply deterministic canonical formatting without claiming identity resolution."""

    attributes = attributes or {}
    text = " ".join(value.strip().split())
    if entity_type is EntityType.PERSON:
        parts = [text.upper()]
        if attributes.get("dob"):
            parts.append(attributes["dob"])
        if attributes.get("father_name"):
            parts.append(attributes["father_name"].upper())
        return "|".join(parts)
    if entity_type is EntityType.PHONE:
        digits = re.sub(r"\D", "", text)
        if digits.startswith("0") and len(digits) == 11:
            digits = "91" + digits[1:]
        if len(digits) == 10:
            digits = "91" + digits
        if len(digits) != 12 or not digits.startswith("91"):
            raise ValueError("Phone must normalize to a 10-digit Indian number.")
        return "+" + digits
    if entity_type is EntityType.VEHICLE:
        return re.sub(r"[^A-Z0-9]", "", text.upper())
    if entity_type is EntityType.UPI:
        return text.lower()
    if entity_type is EntityType.BANK_ACCOUNT:
        if ":" not in text:
            raise ValueError("Bank account canonical form requires IFSC:ACCOUNT_NUMBER.")
        ifsc, account = text.split(":", 1)
        return f"{ifsc.strip().upper()}:{account.strip()}"
    if entity_type is EntityType.LOCATION:
        lat, lng = (Decimal(part.strip()) for part in text.split(",", 1))
        quantizer = Decimal("0.000001")
        return f"{lat.quantize(quantizer, rounding=ROUND_HALF_UP):f},{lng.quantize(quantizer, rounding=ROUND_HALF_UP):f}"
    if entity_type is EntityType.FIR:
        return text.upper()
    if entity_type in {EntityType.ORGANIZATION, EntityType.POLICE_STATION, EntityType.CRIME_CATEGORY}:
        return text.upper()
    return text


def validate_relationship_endpoints(
    relationship_type: RelationshipType,
    source_type: EntityType,
    target_type: EntityType,
) -> None:
    sources, targets = RELATIONSHIP_ENDPOINTS[relationship_type]
    if source_type not in sources or target_type not in targets:
        raise ValueError(
            f"{relationship_type.value} does not allow {source_type.value} -> {target_type.value}."
        )


def schema_entity_type(value: str) -> EntityType:
    """Parse only database-schema entity types, rejecting pending extensions."""

    if value in SCHEMA_EXTENSION_ENTITY_TYPES:
        raise ValueError(f"{value} requires an explicit schema extension before persistence.")
    return EntityType(value)
