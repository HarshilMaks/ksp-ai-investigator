"""Synchronous deterministic fast path with mandatory evidence release gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.domain.evidence import EvidenceDecision
from src.engines.evidence import EvidenceGate
from src.registry.manifest import get_tool_spec
from src.registry.schemas import ToolCall
from src.registry.tools import AuthorizationContext, RegistryError, ToolDispatcher

from .router import FastPathRouter


class FastPathError(RegistryError):
    """The request cannot use the synchronous deterministic fast path."""


@dataclass(frozen=True)
class FastPathResponse:
    route: str
    released: bool
    tool_id: str
    data: dict[str, Any]
    citations: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    uncertainty: dict[str, Any]
    audit: dict[str, Any]


class FastPathExecutor:
    """Run one deterministic tool, then release only evidence-gated output."""

    def __init__(
        self,
        dispatcher: ToolDispatcher,
        *,
        router: FastPathRouter | None = None,
        evidence_gate: EvidenceGate | None = None,
    ) -> None:
        self.dispatcher = dispatcher
        self.router = router or FastPathRouter()
        self.evidence_gate = evidence_gate or EvidenceGate()

    async def execute(
        self,
        call: ToolCall | Mapping[str, Any],
        *,
        authorization: AuthorizationContext,
        request_id: str | None = None,
    ) -> FastPathResponse:
        decision = self.router.classify(call)
        if decision.route != "fast" or decision.tool_id is None:
            raise FastPathError(
                "FAST_PATH_NOT_SUPPORTED",
                "Request must use a supported deterministic fast-path tool.",
                details={"route": decision.route, "tool_id": decision.tool_id, "reason": decision.reason},
            )
        output = await self.dispatcher.dispatch(call, authorization=authorization)
        spec = get_tool_spec(output.tool_id)
        evidence: EvidenceDecision = self.evidence_gate.validate(
            output,
            spec=spec,
            authorization=authorization,
            request_id=request_id,
        )
        return FastPathResponse(
            route="fast",
            released=evidence.released,
            tool_id=output.tool_id,
            data=output.model_dump(mode="json"),
            citations=evidence.citations,
            warnings=evidence.warnings,
            errors=evidence.errors,
            uncertainty=dict(evidence.uncertainty),
            audit={
                "request_id": evidence.audit.request_id,
                "officer_id": evidence.audit.officer_id,
                "tool_id": evidence.audit.tool_id,
                "route": evidence.audit.route,
                "checked_at": evidence.audit.checked_at,
                "source_count": evidence.audit.source_count,
                "claim_count": evidence.audit.claim_count,
            },
        )
