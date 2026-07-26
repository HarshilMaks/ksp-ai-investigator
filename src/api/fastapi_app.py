"""Real FastAPI deployment adapter over the typed P10 application core."""

from __future__ import annotations

from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse

from .application import ApiApplication
from .types import ApiRequest


def create_fastapi_app(application: ApiApplication, *, title: str = "KSP InvestigateAI API") -> FastAPI:
    """Mount every versioned API request through FastAPI.

    Business behavior remains in ``ApiApplication``; FastAPI owns HTTP request
    parsing, response transport, OpenAPI hosting, and deployment integration.
    SSE responses use ``StreamingResponse`` so the deployment boundary is a
    native FastAPI application rather than only a raw ASGI callable.
    """

    app = FastAPI(title=title, version="1.0.0", docs_url="/docs", redoc_url="/redoc")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def dispatch(request: Request, path: str) -> Response:
        query = request.url.query
        request_path = request.url.path + (f"?{query}" if query else "")
        typed_request = ApiRequest(request.method, request_path, dict(request.headers), await request.body())
        typed_response = await application.handle(typed_request)
        headers = dict(typed_response.headers)
        content_type = headers.pop("content-type", "")
        if content_type.startswith("text/event-stream"):
            headers["content-type"] = content_type
            return StreamingResponse(iter((typed_response.body,)), status_code=typed_response.status, headers=headers, media_type=None)
        if content_type:
            headers["content-type"] = content_type
        return Response(content=typed_response.body, status_code=typed_response.status, headers=headers, media_type=None)

    return app


__all__ = ["create_fastapi_app"]
