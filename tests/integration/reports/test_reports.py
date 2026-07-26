from __future__ import annotations

import unittest
from src.registry.tools import AuthorizationContext
from src.services.reports import EvidencePackage, ReportService


class ReportBoundaryTests(unittest.TestCase):
    def test_report_requires_citations_classification_and_human_review(self) -> None:
        service = ReportService()
        auth = AuthorizationContext("officer-1", "IO", frozenset({"investigation:read"}), investigation_id="I1")
        package = EvidencePackage("I1", "Synthetic investigation", "Evidence-backed summary", ({"source_id": "fir-1", "locator": "record:1"},), ("Observed event",), ("Model assets unavailable",))
        report = service.generate(package, authorization=auth)
        self.assertEqual("RESTRICTED", report.classification)
        self.assertTrue(report.requires_human_review)
        self.assertIn("HUMAN REVIEW REQUIRED", report.content)
        self.assertIn("fir-1", report.content)
        self.assertIn("not a legal conclusion", report.content)

    def test_report_rejects_uncited_or_cross_scope_packages(self) -> None:
        service = ReportService()
        auth = AuthorizationContext("officer-1", "IO", frozenset({"investigation:read"}), investigation_id="I1")
        with self.assertRaises(ValueError):
            service.generate(EvidencePackage("I1", "Title", "Summary", ()), authorization=auth)
        with self.assertRaises(PermissionError):
            service.generate(EvidencePackage("I2", "Title", "Summary", ({"source_id": "s", "locator": "l"},)), authorization=auth)


if __name__ == "__main__":
    unittest.main()
