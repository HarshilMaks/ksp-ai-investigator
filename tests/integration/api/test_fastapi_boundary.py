from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI

from src.api import ApiAuthenticator, ApiApplication, StaticAuthVerifier, create_fastapi_app
from src.services.checkpoints import LocalCheckpointStore
from src.services.investigations import InvestigationService


async def invoke(app: FastAPI, method: str, path: str, body: dict | None = None) -> tuple[int, dict[str, str], bytes]:
    raw = b"" if body is None else json.dumps(body).encode()
    messages = [{"type": "http.request", "body": raw, "more_body": False}]
    response: dict[str, object] = {"body": b"", "headers": {}}

    async def receive() -> dict[str, object]:
        return messages.pop(0)

    async def send(message: dict[str, object]) -> None:
        if message["type"] == "http.response.start":
            response["status"] = message["status"]
            response["headers"] = {key.decode(): value.decode() for key, value in message["headers"]}  # type: ignore[index]
        elif message["type"] == "http.response.body":
            response["body"] += message.get("body", b"")  # type: ignore[operator]

    await app({"type": "http", "method": method, "path": path, "query_string": b"", "headers": [(b"authorization", b"Bearer token"), (b"content-type", b"application/json")], "scheme": "http", "server": ("test", 80), "client": ("test", 1), "http_version": "1.1"}, receive, send)
    return int(response["status"]), response["headers"], response["body"]  # type: ignore[return-value]


class FastApiBoundaryTests(unittest.TestCase):
    def test_real_fastapi_app_mounts_typed_api_application(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verifier = StaticAuthVerifier({"token": {"officer_id": str(uuid4()), "role": "IO", "scopes": ["investigation:read", "investigation:write"]}})
            core = ApiApplication(InvestigationService(LocalCheckpointStore(Path(directory))), ApiAuthenticator(verifier))
            app = create_fastapi_app(core)
            self.assertIsInstance(app, FastAPI)
            status, headers, body = asyncio.run(invoke(app, "POST", "/api/v1/investigations", {"title": "FastAPI boundary test"}))
            self.assertEqual(201, status)
            self.assertEqual("application/json; charset=utf-8", headers["content-type"])
            self.assertIn("investigation_id", json.loads(body)["data"])

    def test_fastapi_exposes_openapi_and_preserves_sse_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verifier = StaticAuthVerifier({"token": {"officer_id": str(uuid4()), "role": "IO", "scopes": ["investigation:read", "investigation:write"]}})
            app = create_fastapi_app(ApiApplication(InvestigationService(LocalCheckpointStore(Path(directory))), ApiAuthenticator(verifier)))
            paths = app.openapi()["paths"]
            self.assertIn("/{path}", paths)
            self.assertTrue(any(route.path == "/{path:path}" for route in app.routes))


if __name__ == "__main__":
    unittest.main()
