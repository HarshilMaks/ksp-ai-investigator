"""Deterministic synthetic FIR generation using Karnataka/CCTNS formats."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from src.domain.enums import FIRStatus, Priority
from src.domain.models import FIR

from .karnataka_context import CRIME_CATEGORIES, STATIONS, SYNTHETIC_MARKER

IST = timezone(timedelta(hours=5, minutes=30))


def _id(seed: int, index: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"ksp-investigateai:synthetic:{seed}:fir:{index}")


def generate_firs(count: int = 10, *, seed: int = 20260725, year: int = 2026) -> list[FIR]:
    """Return reproducible FIR records with no real personal data."""

    if count < 0:
        raise ValueError("count must be non-negative")
    if not 2000 <= year <= 2100:
        raise ValueError("year must be a four-digit fixture year")
    base = datetime(year, 1, 1, 8, 0, tzinfo=IST)
    firs: list[FIR] = []
    for index in range(1, count + 1):
        station = STATIONS[(index - 1) % len(STATIONS)]
        category, sections, mo = CRIME_CATEGORIES[(index - 1) % len(CRIME_CATEGORIES)]
        crime_date = base + timedelta(days=(index - 1) * 7, hours=index % 8)
        registration_date = crime_date + timedelta(hours=2)
        status = FIRStatus.UNDER_INVESTIGATION if index % 3 else FIRStatus.OPEN
        priority = Priority.HIGH if category in {"Cybercrime", "Fraud/Cheating"} else Priority.MEDIUM
        serial = f"{index:06d}"
        firs.append(
            FIR(
                fir_id=_id(seed, index),
                fir_number=f"KA/{station.district_code}/{station.station_number}/{year}/{serial}",
                ps_code=station.ps_code,
                district=station.district,
                crime_date=crime_date,
                registration_date=registration_date,
                ipc_sections=tuple(sections),
                crime_category=category,
                crime_subtype="synthetic-demo",
                narrative_en=(
                    f"{SYNTHETIC_MARKER}: synthetic {category.lower()} incident {index:04d}; "
                    f"modus operandi: {mo}."
                ),
                narrative_kn=None,
                status=status,
                priority=priority,
                modus_operandi={"method": mo, "synthetic": True},
                complainant_name=f"Synthetic Complainant {index:04d}",
            )
        )
    return firs
