"""Fail-closed dispatch for the internal T01–T23 registry.

The dispatcher has no database, Cypher, HTTP, or model-provider access. Concrete
engine handlers are injected by later phases; this keeps registry authorization
and validation independent from engine implementation.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping

from pydantic import BaseModel, ValidationError

from src.shared.errors import ApplicationError

from .manifest import EXPECTED_TOOL_IDS, ToolSpec, get_tool_spec
from .schemas import RegistryModel, ToolCall, ToolOutput

ToolHandler = Callable[[RegistryModel, "AuthorizationContext"], ToolOutput | Mapping[str, Any] | Awaitable[ToolOutput | Mapping[str, Any]]]


class RegistryError(ApplicationError):
    """Safe registry validation, authorization, or execution failure."""


@dataclass(frozen=True)
class AuthorizationContext:
    officer_id: str
    role: str
    scopes: frozenset[str] = frozenset()
    allowed_tool_ids: frozenset[str] | None = None
    investigation_id: str | None = None

    def permits(self, spec: ToolSpec) -> bool:
        if self.allowed_tool_ids is not None and spec.tool_id not in self.allowed_tool_ids:
            return False
        return set(spec.required_permissions).issubset(self.scopes)


@dataclass(frozen=True)
class DispatchRecord:
    tool_id: str
    tool_name: str
    owner: str
    officer_id: str
    timeout_ms: int
    citations_required: bool


@dataclass
class ToolDispatcher:
    """Validate and invoke only registered, authorized, injected tool handlers."""

    handlers: dict[str, ToolHandler] = field(default_factory=dict)
    records: list[DispatchRecord] = field(default_factory=list)

    def register(self, tool_id: str, handler: ToolHandler) -> None:
        spec = _safe_spec(tool_id)
        if not callable(handler):
            raise RegistryError("REGISTRY_INVALID_HANDLER", "A tool handler must be callable.")
        self.handlers[spec.tool_id] = handler

    def validate_call(self, call: ToolCall | Mapping[str, Any]) -> tuple[ToolCall, ToolSpec, RegistryModel]:
        request = _parse_call(call)
        spec = _safe_spec(request.tool_id)
        if request.tool_name != spec.name:
            raise RegistryError(
                "REGISTRY_TOOL_NAME_MISMATCH",
                "tool_name does not match the registered tool ID.",
                details={"tool_id": spec.tool_id, "expected": spec.name},
            )
        if request.timeout_ms > spec.max_timeout_ms:
            raise RegistryError(
                "REGISTRY_TIMEOUT_LIMIT",
                "Requested timeout exceeds the tool budget.",
                details={"tool_id": spec.tool_id, "maximum_ms": spec.max_timeout_ms},
            )
        try:
            parameters = spec.input_model.model_validate(request.parameters)
        except ValidationError as exc:
            raise RegistryError(
                "REGISTRY_INVALID_INPUT",
                "Tool parameters failed the registered schema.",
                details={"tool_id": spec.tool_id, "errors": exc.errors(include_url=False)},
            ) from exc
        return request, spec, parameters

    async def dispatch(
        self,
        call: ToolCall | Mapping[str, Any],
        *,
        authorization: AuthorizationContext,
        public_route: bool = False,
    ) -> ToolOutput:
        request, spec, parameters = self.validate_call(call)
        if public_route or spec.public_route:
            raise RegistryError(
                "REGISTRY_PUBLIC_ROUTE_FORBIDDEN",
                "Internal tools cannot be invoked through a public route.",
                details={"tool_id": spec.tool_id},
            )
        if not authorization.permits(spec):
            raise RegistryError(
                "REGISTRY_UNAUTHORIZED",
                "Authorization context cannot invoke this tool.",
                details={"tool_id": spec.tool_id, "role": authorization.role},
            )
        handler = self.handlers.get(spec.tool_id)
        if handler is None:
            raise RegistryError(
                "REGISTRY_HANDLER_UNAVAILABLE",
                "No engine handler has been registered for this tool.",
                details={"tool_id": spec.tool_id, "owner": spec.owner},
            )
        try:
            result = handler(parameters, authorization)
            if inspect.isawaitable(result):
                result = await asyncio.wait_for(result, timeout=request.timeout_ms / 1000)
            output = spec.output_model.model_validate(result)
        except asyncio.TimeoutError as exc:
            raise RegistryError(
                "REGISTRY_EXECUTION_TIMEOUT",
                "Tool execution exceeded its request timeout.",
                details={"tool_id": spec.tool_id, "timeout_ms": request.timeout_ms},
            ) from exc
        except ValidationError as exc:
            raise RegistryError(
                "REGISTRY_INVALID_OUTPUT",
                "Tool handler output failed the registered output schema.",
                details={"tool_id": spec.tool_id, "errors": exc.errors(include_url=False)},
            ) from exc
        self.records.append(
            DispatchRecord(
                tool_id=spec.tool_id,
                tool_name=spec.name,
                owner=spec.owner,
                officer_id=authorization.officer_id,
                timeout_ms=request.timeout_ms,
                citations_required=spec.citation_required,
            )
        )
        return output


def _parse_call(call: ToolCall | Mapping[str, Any]) -> ToolCall:
    if isinstance(call, ToolCall):
        return call
    if isinstance(call, BaseModel):
        call = call.model_dump()
    if isinstance(call, Mapping):
        raw_tool_id = call.get("tool_id")
        if isinstance(raw_tool_id, str) and raw_tool_id not in EXPECTED_TOOL_IDS:
            raise RegistryError(
                "REGISTRY_UNKNOWN_TOOL",
                "The requested tool is not registered.",
                details={"tool_id": raw_tool_id},
            )
    try:
        return ToolCall.model_validate(call)
    except ValidationError as exc:
        raise RegistryError(
            "REGISTRY_INVALID_CALL",
            "Tool call failed the base registry schema.",
            details={"errors": exc.errors(include_url=False)},
        ) from exc


def _safe_spec(tool_id: str) -> ToolSpec:
    try:
        return get_tool_spec(tool_id)
    except KeyError as exc:
        raise RegistryError(
            "REGISTRY_UNKNOWN_TOOL",
            "The requested tool is not registered.",
            details={"tool_id": tool_id},
        ) from exc
