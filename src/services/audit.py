"""Tamper-evident SHA-512 audit records owned by the application boundary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from src.shared.masking import redact_secrets


@dataclass(frozen=True)
class AuditRecord:
    sequence: int
    timestamp: datetime
    officer_id: str
    role: str
    operation: str
    resource_type: str
    resource_id: str
    scope: dict[str, str | None]
    outcome: str
    details: dict[str, Any]
    previous_hash: str
    record_hash: str
    human_review_required: bool = True

    def canonical_payload(self) -> bytes:
        payload = {
            "sequence": self.sequence, "timestamp": self.timestamp.isoformat(), "officer_id": self.officer_id,
            "role": self.role, "operation": self.operation, "resource_type": self.resource_type,
            "resource_id": self.resource_id, "scope": self.scope, "outcome": self.outcome,
            "details": redact_secrets(self.details), "previous_hash": self.previous_hash,
            "human_review_required": self.human_review_required,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


class AuditLog:
    def __init__(self, *, clock=None) -> None:
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._records: list[AuditRecord] = []

    def append(self, *, officer_id: str, role: str, operation: str, resource_type: str, resource_id: str, scope: dict[str, str | None] | None = None, outcome: str = "success", details: dict[str, Any] | None = None, human_review_required: bool = True) -> AuditRecord:
        previous = self._records[-1].record_hash if self._records else "GENESIS"
        record = AuditRecord(len(self._records) + 1, self.clock(), officer_id, role, operation, resource_type, resource_id, dict(scope or {}), outcome, redact_secrets(dict(details or {})), previous, "", human_review_required)
        digest = hashlib.sha512(record.canonical_payload()).hexdigest()
        record = replace(record, record_hash=digest)
        self._records.append(record)
        return record

    def verify(self) -> bool:
        previous = "GENESIS"
        for expected_sequence, record in enumerate(self._records, 1):
            if record.sequence != expected_sequence or record.previous_hash != previous:
                return False
            if hashlib.sha512(record.canonical_payload()).hexdigest() != record.record_hash:
                return False
            previous = record.record_hash
        return True

    @property
    def records(self) -> tuple[AuditRecord, ...]:
        return tuple(self._records)


__all__ = ["AuditLog", "AuditRecord"]
