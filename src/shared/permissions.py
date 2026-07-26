"""Application-level RBAC/scope checks; Catalyst/Hexel remain policy authorities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.registry.tools import AuthorizationContext


class Operation(str, Enum):
    READ = "read"
    MUTATE = "mutate"
    TOOL = "tool"
    AGENT = "agent"
    CARD = "card"
    ALERT = "alert"
    EXPORT = "export"
    REPORT = "report"


@dataclass(frozen=True)
class ScopedResource:
    investigation_id: str | None = None
    station_id: str | None = None
    district_id: str | None = None


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str
    masked: bool = False


ROLE_OPERATIONS: dict[str, frozenset[Operation]] = {
    "SHO": frozenset(Operation),
    "IO": frozenset({Operation.READ, Operation.MUTATE, Operation.TOOL, Operation.AGENT, Operation.CARD, Operation.ALERT, Operation.EXPORT, Operation.REPORT}),
    "DCP": frozenset(Operation),
    "Analyst": frozenset({Operation.READ, Operation.TOOL, Operation.CARD}),
    "SP": frozenset(Operation),
}


def authorize(
    context: AuthorizationContext,
    operation: Operation,
    resource: ScopedResource = ScopedResource(),
    *,
    resource_station_id: str | None = None,
    resource_district_id: str | None = None,
) -> PermissionDecision:
    role = context.role.strip()
    if role not in ROLE_OPERATIONS or operation not in ROLE_OPERATIONS[role]:
        return PermissionDecision(False, "role is not permitted for this operation")
    if resource.investigation_id and context.investigation_id and resource.investigation_id != context.investigation_id:
        return PermissionDecision(False, "investigation scope does not match")
    if resource.investigation_id and context.investigation_id is None and "investigation:read" not in context.scopes and "investigation:write" not in context.scopes:
        return PermissionDecision(False, "investigation scope is required")
    if resource_station_id and "station:*" not in context.scopes and f"station:{resource_station_id}" not in context.scopes and role not in {"DCP", "SP"}:
        return PermissionDecision(False, "station scope does not match")
    if resource_district_id and "district:*" not in context.scopes and f"district:{resource_district_id}" not in context.scopes and role != "SP":
        return PermissionDecision(False, "district scope does not match")
    return PermissionDecision(True, "authorized", masked=role == "Analyst")


def require_authorized(context: AuthorizationContext, operation: Operation, resource: ScopedResource = ScopedResource(), **kwargs: str | None) -> None:
    decision = authorize(context, operation, resource, **kwargs)
    if not decision.allowed:
        raise PermissionError(decision.reason)


__all__ = ["Operation", "PermissionDecision", "ROLE_OPERATIONS", "ScopedResource", "authorize", "require_authorized"]
