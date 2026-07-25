"""Deterministic synthetic entity generation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from src.domain.enums import EntityType
from src.domain.models import Entity
from src.domain.ontology import canonicalize


def _id(seed: int, kind: str, index: int):
    return uuid5(NAMESPACE_URL, f"ksp-investigateai:synthetic:{seed}:{kind}:{index}")


def generate_entities(count: int = 10, *, seed: int = 20260725, observed_at: datetime | None = None) -> list[Entity]:
    """Generate deterministic, clearly synthetic entities."""

    if count < 0:
        raise ValueError("count must be non-negative")
    timestamp = observed_at or datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc)
    entities: list[Entity] = []
    for index in range(1, count + 1):
        person_value = f"Synthetic Person {index:04d}"
        entities.append(
            Entity(
                entity_id=_id(seed, "person", index),
                entity_type=EntityType.PERSON,
                entity_value=person_value,
                canonical_value=canonicalize(
                    EntityType.PERSON,
                    person_value,
                    attributes={"dob": f"1990-01-{(index % 28) + 1:02d}", "father_name": "Synthetic Parent"},
                ),
                attributes={"synthetic": True, "role": "ACCUSED"},
            )
        )
        phone = f"+9100000{index:05d}"
        entities.append(
            Entity(
                entity_id=_id(seed, "phone", index),
                entity_type=EntityType.PHONE,
                entity_value=phone,
                canonical_value=canonicalize(EntityType.PHONE, phone),
                attributes={"synthetic": True, "carrier": "Synthetic Carrier"},
            )
        )
        vehicle = f"KA-00-SY-{index:04d}"
        entities.append(
            Entity(
                entity_id=_id(seed, "vehicle", index),
                entity_type=EntityType.VEHICLE,
                entity_value=vehicle,
                canonical_value=canonicalize(EntityType.VEHICLE, vehicle),
                attributes={"synthetic": True, "make": "Synthetic Motors", "model": "Demo"},
            )
        )
        upi = f"synthetic{index:04d}@demo"
        entities.append(
            Entity(
                entity_id=_id(seed, "upi", index),
                entity_type=EntityType.UPI,
                entity_value=upi,
                canonical_value=canonicalize(EntityType.UPI, upi),
                attributes={"synthetic": True, "provider": "demo"},
            )
        )
    return entities
