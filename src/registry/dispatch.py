"""Public Python entry points for internal registry dispatch."""

from __future__ import annotations

from typing import Any, Mapping

from .tools import AuthorizationContext, ToolDispatcher, ToolHandler


def build_dispatcher(handlers: Mapping[str, ToolHandler] | None = None) -> ToolDispatcher:
    dispatcher = ToolDispatcher()
    for tool_id, handler in (handlers or {}).items():
        dispatcher.register(tool_id, handler)
    return dispatcher


async def dispatch_tool(
    dispatcher: ToolDispatcher,
    call: Mapping[str, Any],
    *,
    authorization: AuthorizationContext,
    public_route: bool = False,
):
    """Dispatch one internal call after schema, budget, route, and auth checks."""

    return await dispatcher.dispatch(call, authorization=authorization, public_route=public_route)
