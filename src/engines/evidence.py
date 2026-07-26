"""Mandatory evidence/explainability gate for released deterministic results."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.domain.evidence import EvidenceAuditMetadata, EvidenceClaim, EvidenceDecision
from src.registry.manifest import ToolSpec
from src.registry.schemas import ToolOutput
from src.registry.tools import AuthorizationContext


class EvidenceGate:
    """Validate a tool result before it can be released to a caller."""

    def validate(
        self,
        output: ToolOutput,
        *,
        spec: ToolSpec,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> EvidenceDecision:
        errors: list[str] = []
        warnings = list(output.warnings)
        citations = tuple(citation.model_dump() for citation in output.citations)
        data = output.data
        records = _records(data)

        if not authorization.officer_id.strip() or not authorization.permits(spec):
            errors.append("authorization context is not permitted for this tool")
        if output.status == "failed":
            errors.append("tool returned a failed status")
        if spec.citation_required and records and not citations:
            errors.append("result contains records but no citations")
        if records and citations and len(citations) < len(records):
            errors.append("citation coverage is incomplete for returned records")
        if hasattr(output, "total"):
            total = getattr(output, "total")
            if isinstance(total, int) and total < len(records):
                errors.append("reported total is smaller than returned record count")

        contradictions = _contradictions(data)
        if contradictions:
            warnings.append(f"{len(contradictions)} contradiction(s) surfaced")
            errors.append("unresolved contradictions prevent release")

        claims = _claims_from_data(records, citations, output.tool_id)
        if records and not claims:
            errors.append("factual records could not be converted into cited claims")
        uncertainty = _uncertainty(data, degraded=bool(getattr(output, "degraded", False)))
        audit = EvidenceAuditMetadata(
            request_id=request_id or str(uuid4()),
            officer_id=authorization.officer_id,
            tool_id=output.tool_id,
            source_count=len(citations),
            claim_count=len(claims),
        )
        return EvidenceDecision(
            released=not errors,
            claims=tuple(claims),
            citations=citations,
            warnings=tuple(warnings),
            errors=tuple(errors),
            uncertainty=uncertainty,
            audit=audit,
        )


def _records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return [item for item in data["records"] if isinstance(item, dict)]
    return []


def _claims_from_data(
    records: list[dict[str, Any]],
    citations: tuple[dict[str, Any], ...],
    tool_id: str,
) -> list[EvidenceClaim]:
    citation_ids = tuple(str(citation["source_id"]) for citation in citations if citation.get("source_id"))
    claims: list[EvidenceClaim] = []
    for index, record in enumerate(records, start=1):
        source_ids = tuple(
            str(record[key])
            for key in ("fir_id", "entity_id", "relationship_id", "source_id", "id")
            if record.get(key) is not None
        )
        claims.append(
            EvidenceClaim(
                claim_id=f"{tool_id}:claim:{index}",
                text=f"Deterministic tool result {index} returned.",
                source_ids=source_ids or citation_ids,
                uncertainty={"type": "deterministic_engine", "tool_id": tool_id},
            )
        )
    return claims


def _contradictions(data: Any) -> list[Any]:
    if isinstance(data, dict) and isinstance(data.get("contradictions"), list):
        return data["contradictions"]
    return []


def _uncertainty(data: Any, *, degraded: bool) -> dict[str, Any]:
    if isinstance(data, dict) and isinstance(data.get("uncertainty"), dict):
        return dict(data["uncertainty"])
    if degraded:
        return {"type": "degraded", "note": "A dependency was unavailable; local fallback was used."}
    return {"type": "deterministic_engine", "note": "No probabilistic claim was introduced by the fast path."}
