"""Deterministic fast/deep route classification for P08."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from pydantic import ValidationError

from src.registry.manifest import get_tool_spec
from src.registry.schemas import ToolCall

FAST_PATH_TOOL_IDS = frozenset({"T01", "T02", "T03", "T06", "T13", "T14"})


@dataclass(frozen=True)
class RouteDecision:
    route: Literal["fast", "deep", "reject"]
    tool_id: str | None
    reason: str


class FastPathRouter:
    """Allow only exact/structured deterministic tools on the synchronous path."""

    def classify(self, call: ToolCall | Mapping[str, Any]) -> RouteDecision:
        try:
            request = call if isinstance(call, ToolCall) else ToolCall.model_validate(call)
            spec = get_tool_spec(request.tool_id)
        except (ValidationError, KeyError):
            return RouteDecision("reject", None, "tool call is not a registered typed request")
        if request.tool_name != spec.name:
            return RouteDecision("reject", spec.tool_id, "tool name does not match tool ID")
        if spec.tool_id not in FAST_PATH_TOOL_IDS:
            return RouteDecision("deep", spec.tool_id, "tool requires a deep path or reasoning stage")
        return RouteDecision("fast", spec.tool_id, "exact/structured deterministic tool")

    def classify_text(self, query: str) -> RouteDecision:
        """Natural-language text is never guessed into a tool call on the fast path."""

        if not query or not query.strip():
            return RouteDecision("reject", None, "query is empty")
        return RouteDecision("deep", None, "natural-language intent requires validated planning")
