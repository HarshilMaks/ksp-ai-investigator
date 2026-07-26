from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timezone

from src.registry.tools import AuthorizationContext
from src.services.audit import AuditLog
from src.shared.masking import mask_record, redact_secrets
from src.shared.permissions import Operation, ScopedResource, authorize


class GovernanceTests(unittest.TestCase):
    def test_role_matrix_and_investigation_scope_fail_closed(self) -> None:
        analyst = AuthorizationContext("a", "Analyst", frozenset({"station:S1", "investigation:read"}), investigation_id="I1")
        self.assertTrue(authorize(analyst, Operation.READ, ScopedResource("I1"), resource_station_id="S1").allowed)
        self.assertFalse(authorize(analyst, Operation.EXPORT, ScopedResource("I1"), resource_station_id="S1").allowed)
        self.assertFalse(authorize(analyst, Operation.READ, ScopedResource("I2"), resource_station_id="S1").allowed)
        self.assertFalse(authorize(analyst, Operation.READ, ScopedResource("I1"), resource_station_id="S2").allowed)

    def test_analyst_masking_and_secret_redaction(self) -> None:
        record = {"name": "Synthetic Officer", "phone": "9876543210", "account_number": "123456789", "summary": "synthetic", "nested": [{"address": "Synthetic Address"}], "token": "secret-token"}
        masked = mask_record(record, role="Analyst")
        self.assertEqual("[MASKED]", masked["name"])
        self.assertEqual("******3210", masked["phone"])
        self.assertEqual("*****6789", masked["account_number"])
        self.assertEqual("synthetic", masked["summary"])
        self.assertEqual("[MASKED]", masked["nested"][0]["address"])
        self.assertEqual("[REDACTED]", redact_secrets(record)["token"])
        self.assertEqual(record, mask_record(record, role="IO"))

    def test_sha512_hash_chain_verifies_and_detects_tampering(self) -> None:
        clock = lambda: datetime(2026, 7, 26, tzinfo=timezone.utc)
        log = AuditLog(clock=clock)
        first = log.append(officer_id="o1", role="IO", operation="read", resource_type="investigation", resource_id="I1", scope={"station": "S1"}, details={"token": "must-not-hash-in-clear"})
        log.append(officer_id="o1", role="IO", operation="export", resource_type="report", resource_id="R1", scope={"station": "S1"}, outcome="review_required")
        self.assertTrue(log.verify())
        self.assertEqual("GENESIS", first.previous_hash)
        tampered = replace(log.records[0], details={"outcome": "changed"})
        log._records[0] = tampered  # test-only corruption of the in-memory boundary
        self.assertFalse(log.verify())


if __name__ == "__main__":
    unittest.main()
