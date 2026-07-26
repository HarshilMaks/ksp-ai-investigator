from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from src.api import ApiApplication, ApiAuthenticator, ApiRequest, MultipartParser, StaticAuthVerifier
from src.domain.investigation_state import InvestigationState
from src.registry import AuthorizationContext, ToolDispatcher
from src.services.checkpoints import LocalCheckpointStore
from src.services.investigations import InvestigationService
from src.orchestration.fast_path import FastPathExecutor


class FakeRunner:
    async def run(self, state: InvestigationState) -> InvestigationState:
        return replace(state, version=state.version)


def payload(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


class ApiApplicationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.owner_id = uuid4()
        self.verifier = StaticAuthVerifier(
            {
                "token": {
                    "officer_id": str(self.owner_id),
                    "role": "IO",
                    "scopes": ["investigation:read", "investigation:write", "ontology:read"],
                }
            }
        )
        self.authenticator = ApiAuthenticator(self.verifier)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def build_app(self, *, runner=None, fast_path=None, max_upload_bytes=1024) -> ApiApplication:
        service = InvestigationService(LocalCheckpointStore(Path(self.tempdir.name)))
        return ApiApplication(
            service,
            self.authenticator,
            runner=runner,
            fast_path=fast_path,
            multipart=MultipartParser(max_bytes=max_upload_bytes),
        )

    def request(self, method: str, path: str, body: dict | None = None, *, cookie: bool = False, content_type: str = "application/json") -> ApiRequest:
        headers = {"content-type": content_type}
        if cookie:
            headers["cookie"] = "session=token"
        else:
            headers["authorization"] = "Bearer token"
        raw = b"" if body is None else json.dumps(body).encode()
        return ApiRequest(method, path, headers, raw)

    async def create_investigation(self, app: ApiApplication) -> str:
        response = await app.handle(self.request("POST", "/api/v1/investigations", {"title": "API investigation"}))
        self.assertEqual(response.status, 201)
        return payload(response)["data"]["investigation_id"]

    async def test_resource_routes_create_read_and_mutate_with_standard_errors(self) -> None:
        app = self.build_app()
        investigation_id = await self.create_investigation(app)
        read = await app.handle(self.request("GET", f"/api/v1/investigations/{investigation_id}"))
        self.assertEqual(read.status, 200)
        self.assertEqual(payload(read)["data"]["version"], 1)
        update = await app.handle(self.request("POST", f"/api/v1/investigations/{investigation_id}/status", {"status": "ACTIVE"}))
        self.assertEqual(update.status, 200)
        self.assertEqual(payload(update)["data"]["status"], "ACTIVE")
        unauthorized = await app.handle(ApiRequest("GET", f"/api/v1/investigations/{investigation_id}"))
        self.assertEqual(unauthorized.status, 401)
        self.assertEqual(payload(unauthorized)["error"]["code"], "AUTHENTICATION_REQUIRED")
        self.assertIn("x-request-id", unauthorized.headers)

    async def test_fast_path_query_is_synchronous_and_tools_are_not_public_routes(self) -> None:
        dispatcher = ToolDispatcher()
        dispatcher.register(
            "T01",
            lambda parameters, authorization: {
                "tool_id": "T01", "status": "ok", "data": [{"fir_id": "synthetic-fir-1"}], "total": 1,
                "citations": [{"source_type": "FIR", "source_id": "synthetic-fir-1"}],
            },
        )
        app = self.build_app(fast_path=FastPathExecutor(dispatcher))
        investigation_id = await self.create_investigation(app)
        response = await app.handle(self.request("POST", f"/api/v1/investigations/{investigation_id}/query", {
            "tool_call": {"tool_id": "T01", "tool_name": "sql_query", "parameters": {"table": "firs"}},
        }))
        self.assertEqual(response.status, 200)
        self.assertTrue(payload(response)["data"]["released"])
        forbidden = await app.handle(self.request("POST", "/api/v1/tools/T01", {}))
        self.assertEqual(forbidden.status, 403)
        self.assertEqual(payload(forbidden)["error"]["code"], "API_TOOL_ROUTE_FORBIDDEN")

    async def test_complex_run_is_created_by_rest_and_streamed_as_sse(self) -> None:
        app = self.build_app(runner=FakeRunner())
        investigation_id = await self.create_investigation(app)
        created = await app.handle(self.request("POST", f"/api/v1/investigations/{investigation_id}/runs", {"query": "find linked cases"}))
        self.assertEqual(created.status, 202)
        run_id = payload(created)["data"]["run_id"]
        stream = await app.handle(self.request("GET", f"/api/v1/runs/{run_id}/events", cookie=True))
        self.assertEqual(stream.status, 200)
        self.assertEqual(stream.headers["content-type"], "text/event-stream; charset=utf-8")
        text = stream.body.decode()
        self.assertIn("event: plan", text)
        self.assertIn("event: evidence", text)
        self.assertIn("event: done", text)
        self.assertIn('"status":"done"', text)

    async def test_run_without_runner_emits_explicit_error_event(self) -> None:
        app = self.build_app()
        investigation_id = await self.create_investigation(app)
        created = await app.handle(self.request("POST", f"/api/v1/investigations/{investigation_id}/runs", {"query": "complex"}))
        run_id = payload(created)["data"]["run_id"]
        stream = await app.handle(self.request("GET", f"/api/v1/runs/{run_id}/events"))
        text = stream.body.decode()
        self.assertIn("event: error", text)
        self.assertIn("RUNNER_UNAVAILABLE", text)
        self.assertIn("event: done", text)

    async def test_multipart_upload_accepts_allowed_file_and_rejects_size_or_type(self) -> None:
        app = self.build_app(max_upload_bytes=200)
        investigation_id = await self.create_investigation(app)
        boundary = "demo-boundary"
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"note.txt\"\r\n"
            "Content-Type: text/plain\r\n\r\nsynthetic note\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        valid = ApiRequest("POST", f"/api/v1/investigations/{investigation_id}/uploads", {
            "authorization": "Bearer token", "content-type": f"multipart/form-data; boundary={boundary}",
        }, body)
        response = await app.handle(valid)
        self.assertEqual(response.status, 202)
        self.assertEqual(payload(response)["data"]["filename"], "note.txt")
        oversized = await app.handle(ApiRequest(valid.method, valid.path, valid.headers, body + b"x" * 300))
        self.assertEqual(oversized.status, 413)
        bad_type = body.replace(b"text/plain", b"application/x-executable")
        rejected = await app.handle(ApiRequest(valid.method, valid.path, valid.headers, bad_type))
        self.assertEqual(rejected.status, 403)

    async def test_cookie_auth_supports_sse_and_invalid_route_is_standardized(self) -> None:
        app = self.build_app()
        response = await app.handle(ApiRequest("GET", "/api/v1/not-real", {"cookie": "session=token"}))
        self.assertEqual(response.status, 404)
        self.assertEqual(payload(response)["error"]["code"], "API_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
