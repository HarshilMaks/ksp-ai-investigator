"""Deterministic structured FIR retrieval over governed logical records.

This is an engine boundary, not a SQL parser. It accepts an allowlisted filter
contract and can later be backed by Catalyst/ZCQL after capability validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping, Sequence
from uuid import UUID

from data.generator.fixture import SyntheticFixture
from src.domain.models import FIR, to_record
from src.shared.errors import ApplicationError

from .retrieval.types import RetrievalCitation, StructuredQueryResult, StructuredRecord

ALLOWED_FILTERS = frozenset(
    {
        "fir_id", "fir_number", "ps_code", "district", "crime_category",
        "status", "priority", "year", "crime_date_from", "crime_date_to",
        "registration_date_from", "registration_date_to",
    }
)
ALLOWED_ORDER_FIELDS = frozenset({"fir_number", "crime_date", "registration_date", "district", "priority", "status"})
MAX_STRUCTURED_LIMIT = 1000


class StructuredRetrievalError(ApplicationError, ValueError):
    """A structured retrieval request is invalid or uses an unsupported field."""


@dataclass(frozen=True)
class StructuredQuery:
    filters: Mapping[str, Any] = field(default_factory=dict)
    columns: tuple[str, ...] = ("*",)
    limit: int = 100
    order_by: str | None = None

    def __post_init__(self) -> None:
        unknown = set(self.filters) - ALLOWED_FILTERS
        if unknown:
            raise StructuredRetrievalError(
                "RETRIEVAL_UNKNOWN_FILTER",
                "Structured filter is not in the governed allowlist.",
                details={"fields": sorted(unknown)},
            )
        if isinstance(self.limit, bool) or not 1 <= self.limit <= MAX_STRUCTURED_LIMIT:
            raise StructuredRetrievalError(
                "RETRIEVAL_LIMIT_EXCEEDED",
                "Structured result limit is outside the allowed range.",
                details={"maximum": MAX_STRUCTURED_LIMIT},
            )
        if not self.columns or any(not column.strip() for column in self.columns):
            raise StructuredRetrievalError("RETRIEVAL_INVALID_COLUMNS", "columns must be non-empty names.")
        if self.order_by is not None and self.order_by not in ALLOWED_ORDER_FIELDS:
            raise StructuredRetrievalError(
                "RETRIEVAL_INVALID_ORDER",
                "order_by is not in the governed allowlist.",
                details={"allowed": sorted(ALLOWED_ORDER_FIELDS)},
            )


class InMemoryFIRStore:
    """Local authoritative-shaped FIR store used until Catalyst capability is validated."""

    def __init__(self, firs: Iterable[FIR] = ()) -> None:
        self._firs = tuple(firs)

    @classmethod
    def from_fixture(cls, fixture: SyntheticFixture) -> "InMemoryFIRStore":
        return cls(fixture.firs)

    def query(self, request: StructuredQuery) -> StructuredQueryResult:
        matches = [fir for fir in self._firs if _matches(fir, request.filters)]
        if request.order_by:
            matches.sort(key=lambda fir: _order_value(fir, request.order_by))
        records: list[StructuredRecord] = []
        for rank, fir in enumerate(matches[: request.limit], start=1):
            record = to_record(fir)
            if request.columns != ("*",):
                record = {column: record[column] for column in request.columns if column in record}
            records.append(
                StructuredRecord(
                    record=record,
                    rank=rank,
                    citation=RetrievalCitation(source_type="FIR", source_id=str(fir.fir_id)),
                )
            )
        return StructuredQueryResult(
            records=tuple(records),
            total=len(matches),
            filters_applied=dict(request.filters),
            degraded=False,
        )

    def count(self, filters: Mapping[str, Any] | None = None) -> int:
        request = StructuredQuery(filters=filters or {}, columns=("fir_id",), limit=MAX_STRUCTURED_LIMIT)
        return self.query(request).total


class StructuredRetrievalEngine:
    """Typed deterministic structured retrieval facade."""

    def __init__(self, store: InMemoryFIRStore) -> None:
        self.store = store

    def search(
        self,
        *,
        filters: Mapping[str, Any] | None = None,
        columns: Sequence[str] = ("*",),
        limit: int = 100,
        order_by: str | None = None,
    ) -> StructuredQueryResult:
        return self.store.query(
            StructuredQuery(
                filters=filters or {},
                columns=tuple(columns),
                limit=limit,
                order_by=order_by,
            )
        )


def _matches(fir: FIR, filters: Mapping[str, Any]) -> bool:
    for field, expected in filters.items():
        if field == "fir_id" and not _uuid_matches(fir.fir_id, expected):
            return False
        if field == "fir_number" and fir.fir_number != str(expected):
            return False
        if field == "ps_code" and fir.ps_code != str(expected):
            return False
        if field == "district" and fir.district != str(expected):
            return False
        if field == "crime_category" and fir.crime_category != str(expected):
            return False
        if field == "status" and fir.status.value != str(expected):
            return False
        if field == "priority" and fir.priority.value != str(expected):
            return False
        if field == "year" and fir.registration_date.year != int(expected):
            return False
        if field == "crime_date_from" and fir.crime_date < _parse_datetime(expected):
            return False
        if field == "crime_date_to" and fir.crime_date > _parse_datetime(expected):
            return False
        if field == "registration_date_from" and fir.registration_date < _parse_datetime(expected):
            return False
        if field == "registration_date_to" and fir.registration_date > _parse_datetime(expected):
            return False
    return True


def _uuid_matches(value: UUID, expected: Any) -> bool:
    return str(value) == str(expected)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise StructuredRetrievalError("RETRIEVAL_INVALID_DATE", "Date filters must be ISO timestamps.") from exc
    if parsed.tzinfo is None:
        raise StructuredRetrievalError("RETRIEVAL_NAIVE_DATE", "Date filters must include a timezone.")
    return parsed


def _order_value(fir: FIR, field: str) -> Any:
    return {
        "fir_number": fir.fir_number,
        "crime_date": fir.crime_date,
        "registration_date": fir.registration_date,
        "district": fir.district,
        "priority": fir.priority.value,
        "status": fir.status.value,
    }[field]
