"""Real FastAPI deployment adapter over the typed P10 application core."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import Response, StreamingResponse

from .application import ApiApplication
from .types import ApiRequest


def create_fastapi_app(application: ApiApplication, *, title: str = "KSP InvestigateAI API") -> FastAPI:
    """Create the native FastAPI facade over the typed P10 application core.

    FastAPI owns HTTP routing, request-body transport, OpenAPI, and response
    streaming. ``ApiApplication`` remains the single business/application
    dispatcher, so the framework migration does not duplicate authorization,
    lifecycle, checkpoint, runner, or evidence-gate behavior.
    """

    app = FastAPI(title=title, version="1.0.0", docs_url="/docs", redoc_url="/redoc")

    @app.get("/health", tags=["system"], name="health", operation_id="health")
    async def health() -> dict[str, str]:
        """Return process liveness for browser, load balancer, and deployment checks."""

        return {"status": "ok", "service": "ksp-investigateai"}

    router = APIRouter(prefix=ApiApplication.version_prefix)

    async def transport(request: Request) -> Response:
        query = request.url.query
        request_path = request.url.path + (f"?{query}" if query else "")
        typed_request = ApiRequest(request.method, request_path, dict(request.headers), await request.body())
        typed_response = await application.handle(typed_request)
        headers = dict(typed_response.headers)
        content_type = headers.pop("content-type", "")
        if content_type.startswith("text/event-stream"):
            headers["content-type"] = content_type
            return StreamingResponse(
                iter((typed_response.body,)),
                status_code=typed_response.status,
                headers=headers,
                media_type=None,
            )
        if content_type:
            headers["content-type"] = content_type
        return Response(
            content=typed_response.body,
            status_code=typed_response.status,
            headers=headers,
            media_type=None,
        )

    async def dispatch(request: Request) -> Response:
        return await transport(request)

    async def dispatch_investigation(request: Request, investigation_id: str) -> Response:
        del investigation_id
        return await transport(request)

    async def dispatch_run(request: Request, run_id: str) -> Response:
        del run_id
        return await transport(request)

    async def dispatch_fallback(request: Request, path: str) -> Response:
        del path
        return await transport(request)

    route_specs = (
        ("create_investigation", "/investigations", ("POST",), dispatch),
        ("read_investigation", "/investigations/{investigation_id}", ("GET",), dispatch_investigation),
        ("create_run", "/investigations/{investigation_id}/runs", ("POST",), dispatch_investigation),
        ("query_investigation", "/investigations/{investigation_id}/query", ("POST",), dispatch_investigation),
        ("network_analysis", "/investigations/{investigation_id}/network-analysis", ("POST",), dispatch_investigation),
        ("profile_offender", "/investigations/{investigation_id}/profile-offender", ("POST",), dispatch_investigation),
        ("similar_cases", "/investigations/{investigation_id}/similar-cases", ("POST",), dispatch_investigation),
        ("hypothesis_capability", "/investigations/{investigation_id}/hypothesis", ("POST",), dispatch_investigation),
        ("generate_report", "/investigations/{investigation_id}/generate-report", ("POST",), dispatch_investigation),
        ("update_status", "/investigations/{investigation_id}/status", ("POST",), dispatch_investigation),
        ("add_evidence", "/investigations/{investigation_id}/evidence", ("POST",), dispatch_investigation),
        ("add_note", "/investigations/{investigation_id}/notes", ("POST",), dispatch_investigation),
        ("add_hypothesis", "/investigations/{investigation_id}/hypotheses", ("POST",), dispatch_investigation),
        ("add_timeline", "/investigations/{investigation_id}/timeline", ("POST",), dispatch_investigation),
        ("add_lead", "/investigations/{investigation_id}/leads", ("POST",), dispatch_investigation),
        ("update_graph", "/investigations/{investigation_id}/graph", ("POST",), dispatch_investigation),
        ("upload_evidence", "/investigations/{investigation_id}/uploads", ("POST",), dispatch_investigation),
        ("stream_run", "/runs/{run_id}/events", ("GET",), dispatch_run),
    )
    for name, path, methods, endpoint in route_specs:
        router.add_api_route(path, endpoint, methods=list(methods), name=name, operation_id=name)

    # Keep unknown API requests inside the typed core so its request IDs and
    # standardized error envelope remain consistent with the explicit routes.
    router.add_api_route(
        "/{path:path}",
        dispatch_fallback,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        name="api_fallback",
        include_in_schema=False,
    )
    app.include_router(router)
    return app


__all__ = ["create_fastapi_app"]
