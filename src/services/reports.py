"""Evidence-gated, classified report output with human-review qualification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape

from src.registry.tools import AuthorizationContext
from src.shared.permissions import Operation, ScopedResource, authorize


@dataclass(frozen=True)
class EvidencePackage:
    investigation_id: str
    title: str
    summary: str
    citations: tuple[dict[str, str], ...]
    findings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.investigation_id.strip() or not self.title.strip() or not self.summary.strip():
            raise ValueError("report package requires investigation, title, and summary")
        if not self.citations:
            raise ValueError("report package requires citations")
        if any(not citation.get("source_id") or not citation.get("locator") for citation in self.citations):
            raise ValueError("each report citation requires source_id and locator")


@dataclass(frozen=True)
class ReportDocument:
    investigation_id: str
    classification: str
    generated_at: datetime
    content: str
    citations: tuple[dict[str, str], ...]
    requires_human_review: bool = True
    degraded: bool = False


class ReportService:
    def generate(self, package: EvidencePackage, *, authorization: AuthorizationContext, classification: str = "RESTRICTED") -> ReportDocument:
        package.validate()
        if classification not in {"INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("report classification is invalid")
        decision = authorize(authorization, Operation.REPORT, ScopedResource(package.investigation_id))
        if not decision.allowed:
            raise PermissionError(decision.reason)
        citation_lines = "\n".join(f"- [{escape(item['source_id'])}] {escape(item['locator'])}" for item in package.citations)
        findings = "\n".join(f"- {escape(item)}" for item in package.findings) or "- No additional findings were supplied."
        limitations = "\n".join(f"- {escape(item)}" for item in package.limitations) or "- The package contains only the supplied evidence."
        content = (
            f"# {escape(package.title)}\n\n"
            f"**Classification:** {classification}\n\n"
            "**HUMAN REVIEW REQUIRED:** This document is an investigative decision-support draft. "
            "It is not a legal conclusion, custody record, or determination of guilt.\n\n"
            f"## Summary\n{escape(package.summary)}\n\n"
            f"## Findings\n{findings}\n\n"
            f"## Limitations\n{limitations}\n\n"
            f"## Citations\n{citation_lines}\n"
        )
        return ReportDocument(package.investigation_id, classification, datetime.now(timezone.utc), content, package.citations)


__all__ = ["EvidencePackage", "ReportDocument", "ReportService"]
