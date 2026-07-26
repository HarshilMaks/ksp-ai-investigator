"""Minimal dependency-free REST/SSE application boundary for P10."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Mapping, Protocol
from uuid import UUID, NAMESPACE_URL, uuid5, uuid4

from src.domain.investigation_state import InvestigationLifecycle
from src.domain.enums import Priority, TimelineEventType
from src.orchestration.fast_path import FastPathExecutor
from src.services.investigations import InvestigationService
from src.shared.errors import ApplicationError, new_request_id

from .auth import ApiAuthenticator
from .multipart import MultipartParser
from .sse import SSEEvent, SSEStream
from .types import ApiRequest, ApiResponse


class RunnerProtocol(Protocol):
    async def run(self, state: Any) -> Any: ...


@dataclass
class RunRecord:
    run_id: UUID
    investigation_id: UUID
    request: dict[str, Any]
    authorization: Any
    events: list[SSEEvent] = field(default_factory=list)
    status: str = "queued"
    executed: bool = False


class RunStore:
    """Process-local run/event registry; investigation state remains P09 checkpointed."""

    def __init__(self) -> None:
        self._records: dict[UUID, RunRecord] = {}
        self._lock = asyncio.Lock()

    async def create(self, record: RunRecord) -> None:
        async with self._lock:
            self._records[record.run_id] = record

    async def get(self, run_id: UUID) -> RunRecord | None:
        async with self._lock:
            return self._records.get(run_id)


class ApiApplication:
    """Route versioned application resources without depending on LocalRunner."""

    version_prefix = "/api/v1"
    _capabilities = frozenset({"query", "network-analysis", "profile-offender", "similar-cases", "hypothesis", "generate-report"})

    def __init__(
        self,
        investigations: InvestigationService,
        authenticator: ApiAuthenticator,
        *,
        fast_path: FastPathExecutor | None = None,
        runner: RunnerProtocol | None = None,
        run_store: RunStore | None = None,
        multipart: MultipartParser | None = None,
        cors_origin: str = "*",
    ) -> None:
        self.investigations = investigations
        self.authenticator = authenticator
        self.fast_path = fast_path
        self.runner = runner
        self.run_store = run_store or RunStore()
        self.multipart = multipart or MultipartParser()
        self.cors_origin = cors_origin

    async def handle(self, request: ApiRequest) -> ApiResponse:
        request_id = request.headers.get("x-request-id") or new_request_id()
        try:
            if request.method == "OPTIONS":
                return self._common(ApiResponse(status=204, headers={}), request_id)
            authorization = await self.authenticator.authenticate(request.headers)
            response = await self._dispatch(request, authorization, request_id)
            return self._common(response, request_id)
        except ApplicationError as exc:
            payload = exc.to_response().to_dict()
            payload["error"]["request_id"] = request_id
            return self._common(ApiResponse.json(self._status_for(exc.code), payload, request_id=request_id), request_id)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return self._error(400, "API_INVALID_REQUEST", "Request is malformed.", request_id, {"reason": str(exc)})
        except Exception:
            return self._error(500, "API_INTERNAL_ERROR", "The API request could not be completed.", request_id, {})

    async def _dispatch(self, request: ApiRequest, authorization: Any, request_id: str) -> ApiResponse:
        parts = [part for part in request.route.split("/") if part]
        if parts[:2] != ["api", "v1"] or len(parts) < 3:
            raise ApplicationError("API_NOT_FOUND", "API route does not exist.")
        if parts[2] == "tools":
            raise ApplicationError("API_TOOL_ROUTE_FORBIDDEN", "T01-T23 tools are internal and are not public API routes.")
        if parts[2] == "runs" and len(parts) == 5 and parts[4] == "events" and request.method == "GET":
            return await self._stream_run(self._uuid(parts[3], "run_id"), request_id)
        if parts[2] != "investigations":
            raise ApplicationError("API_NOT_FOUND", "API route does not exist.")
        if len(parts) == 3 and request.method == "POST":
            return await self._create_investigation(request, authorization, request_id)
        if len(parts) < 4:
            raise ApplicationError("API_NOT_FOUND", "Investigation resource ID is required.")
        investigation_id = self._uuid(parts[3], "investigation_id")
        if len(parts) == 4 and request.method == "GET":
            state = await self.investigations.get(investigation_id, authorization=authorization)
            return self._json(200, {"data": state.to_record()})
        if len(parts) == 5 and parts[4] == "runs" and request.method == "POST":
            return await self._create_run(investigation_id, request, authorization, request_id)
        if len(parts) == 5 and parts[4] in self._capabilities and request.method == "POST":
            return await self._capability(parts[4], investigation_id, request, authorization, request_id)
        if len(parts) == 5 and parts[4] == "uploads" and request.method == "POST":
            await self.investigations.get(investigation_id, authorization=authorization)
            upload = self.multipart.parse(request.headers, request.body)
            return self._json(202, {"data": {"filename": upload.filename, "content_type": upload.content_type, "size": len(upload.content), "status": "accepted"}})
        if len(parts) == 5 and request.method == "POST":
            return await self._resource_mutation(parts[4], investigation_id, request, authorization, request_id)
        raise ApplicationError("API_NOT_FOUND", "Investigation route does not exist.")

    async def _create_investigation(self, request: ApiRequest, authorization: Any, request_id: str) -> ApiResponse:
        body = self._body(request)
        owner_value = body.get("owner_id")
        if owner_value:
            owner_id = self._uuid(owner_value, "owner_id")
        else:
            try:
                owner_id = UUID(authorization.officer_id)
            except (ValueError, AttributeError):
                owner_id = uuid5(NAMESPACE_URL, f"ksp-officer:{authorization.officer_id}")
        state = await self.investigations.create(
            title=str(body.get("title", "")), owner_id=owner_id, authorization=authorization,
            description=body.get("description"), primary_fir_id=self._optional_uuid(body.get("primary_fir_id")),
            team_ids=tuple(self._uuid(value, "team_id") for value in body.get("team_ids", ())),
            priority=Priority(body.get("priority", Priority.MEDIUM.value)), request_id=request_id,
        )
        return self._json(201, {"data": state.to_record()})

    async def _resource_mutation(self, action: str, investigation_id: UUID, request: ApiRequest, authorization: Any, request_id: str) -> ApiResponse:
        body = self._body(request)
        if action == "status":
            state = await self.investigations.transition(investigation_id, InvestigationLifecycle(body["status"]), authorization=authorization, request_id=request_id)
        elif action == "evidence":
            state = await self.investigations.pin_evidence(
                investigation_id, fir_id=self._optional_uuid(body.get("fir_id")), entity_id=self._optional_uuid(body.get("entity_id")),
                note=body.get("note"), tags=tuple(body.get("tags", ())), relevance_score=float(body.get("relevance_score", 1.0)),
                authorization=authorization, request_id=request_id,
            )
        elif action == "notes":
            state = await self.investigations.add_note(investigation_id, text=str(body.get("text", "")), tags=tuple(body.get("tags", ())), authorization=authorization, request_id=request_id)
        elif action == "hypotheses":
            state = await self.investigations.add_hypothesis(
                investigation_id, statement=str(body.get("statement", "")), supporting_evidence_ids=tuple(body.get("supporting_evidence_ids", ())),
                contradicting_evidence_ids=tuple(body.get("contradicting_evidence_ids", ())), missing_critical_evidence=tuple(body.get("missing_critical_evidence", ())),
                confidence=float(body.get("confidence", 0.0)), authorization=authorization, request_id=request_id,
            )
        elif action == "timeline":
            state = await self.investigations.add_timeline_event(
                investigation_id, event_time=self._datetime(body["event_time"]), event_type=TimelineEventType(body["event_type"]),
                description=str(body.get("description", "")), source_fir_id=self._optional_uuid(body.get("source_fir_id")),
                source_entity_id=self._optional_uuid(body.get("source_entity_id")), confidence=float(body.get("confidence", 1.0)),
                authorization=authorization, request_id=request_id,
            )
        elif action == "leads":
            state = await self.investigations.add_lead(
                investigation_id, title=str(body.get("title", "")), description=str(body.get("description", "")),
                source_ids=tuple(body.get("source_ids", ())), priority=Priority(body.get("priority", Priority.MEDIUM.value)),
                assigned_to=self._optional_uuid(body.get("assigned_to")), authorization=authorization, request_id=request_id,
            )
        elif action == "graph":
            state = await self.investigations.update_graph_view(
                investigation_id, expanded_entity_ids=tuple(self._uuid(value, "expanded_entity_id") for value in body.get("expanded_entity_ids", ())),
                selected_entity_id=self._optional_uuid(body.get("selected_entity_id")), relationship_filters=tuple(body.get("relationship_filters", ())),
                zoom=float(body.get("zoom", 1.0)), center_x=float(body.get("center_x", 0.0)), center_y=float(body.get("center_y", 0.0)),
                authorization=authorization, request_id=request_id,
            )
        else:
            raise ApplicationError("API_NOT_FOUND", "Resource action does not exist.")
        return self._json(200, {"data": state.to_record()})

    async def _capability(self, capability: str, investigation_id: UUID, request: ApiRequest, authorization: Any, request_id: str) -> ApiResponse:
        body = self._body(request)
        if capability == "query" and body.get("tool_call") is not None:
            if self.fast_path is None:
                raise ApplicationError("FAST_PATH_UNAVAILABLE", "The deterministic fast path is not configured.")
            response = await self.fast_path.execute(body["tool_call"], authorization=authorization, request_id=request_id)
            return self._json(200, {"data": asdict(response)})
        return await self._create_run(investigation_id, request, authorization, request_id, capability=capability)

    async def _create_run(self, investigation_id: UUID, request: ApiRequest, authorization: Any, request_id: str, *, capability: str | None = None) -> ApiResponse:
        state = await self.investigations.get(investigation_id, authorization=authorization)
        body = self._body(request)
        run_id = uuid4()
        record = RunRecord(run_id=run_id, investigation_id=investigation_id, request={**body, "capability": capability}, authorization=authorization)
        record.events.append(SSEEvent("plan", {"run_id": str(run_id), "investigation_id": str(investigation_id), "status": "queued", "request_id": request_id}))
        await self.run_store.create(record)
        return self._json(202, {"data": {"run_id": str(run_id), "investigation_id": str(investigation_id), "status": record.status, "stream_url": f"{self.version_prefix}/runs/{run_id}/events", "state_version": state.version}})

    async def _stream_run(self, run_id: UUID, request_id: str) -> ApiResponse:
        record = await self.run_store.get(run_id)
        if record is None:
            raise ApplicationError("RUN_NOT_FOUND", "Investigation run does not exist.")
        if not record.executed:
            record.executed = True
            record.status = "running"
            state = await self.investigations.get(record.investigation_id, authorization=record.authorization)
            if self.runner is None:
                record.status = "error"
                record.events.append(SSEEvent("error", {"code": "RUNNER_UNAVAILABLE", "message": "No Runner implementation is configured for complex runs.", "request_id": request_id}))
            else:
                try:
                    result = await self.runner.run(state)
                    record.status = "done"
                    record.events.append(SSEEvent("evidence", {"run_id": str(run_id), "state_version": getattr(result, "version", None)}))
                except ApplicationError as exc:
                    record.status = "error"
                    record.events.append(SSEEvent("error", {"code": exc.code, "message": exc.message, "request_id": request_id}))
            record.events.append(SSEEvent("done", {"run_id": str(run_id), "status": record.status}))
        return ApiResponse(status=200, body=SSEStream.from_events(record.events).body, headers={"content-type": "text/event-stream; charset=utf-8", "cache-control": "no-cache", "x-request-id": request_id})

    async def __call__(self, scope: Mapping[str, Any], receive: Any, send: Any) -> None:
        headers = {key.decode().lower(): value.decode() for key, value in scope.get("headers", [])}
        chunks: list[bytes] = []
        while True:
            message = await receive()
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        response = await self.handle(ApiRequest(scope.get("method", "GET"), scope.get("path", "/"), headers, b"".join(chunks)))
        await send({"type": "http.response.start", "status": response.status, "headers": [(key.encode(), value.encode()) for key, value in response.headers.items()]})
        await send({"type": "http.response.body", "body": response.body})

    def _json(self, status: int, payload: object) -> ApiResponse:
        return ApiResponse.json(status, payload, request_id="pending")

    def _common(self, response: ApiResponse, request_id: str) -> ApiResponse:
        headers = dict(response.headers)
        headers["x-request-id"] = request_id
        headers.setdefault("access-control-allow-origin", self.cors_origin)
        headers.setdefault("access-control-allow-credentials", "true")
        headers.setdefault("access-control-allow-headers", "Authorization, Content-Type, X-Request-ID")
        headers.setdefault("access-control-allow-methods", "GET, POST, OPTIONS")
        return ApiResponse(response.status, response.body, headers)

    def _error(self, status: int, code: str, message: str, request_id: str, details: dict[str, Any]) -> ApiResponse:
        return self._common(ApiResponse.json(status, {"error": {"code": code, "message": message, "details": details, "request_id": request_id}}, request_id=request_id), request_id)

    @staticmethod
    def _body(request: ApiRequest) -> dict[str, Any]:
        if not request.body:
            return {}
        value = json.loads(request.body.decode("utf-8"))
        if not isinstance(value, dict):
            raise ApplicationError("API_JSON_OBJECT_REQUIRED", "JSON request bodies must be objects.")
        return value

    @staticmethod
    def _uuid(value: Any, name: str, *, fallback: str | None = None) -> UUID:
        raw = fallback if value is None else value
        try:
            return UUID(str(raw))
        except (ValueError, TypeError, AttributeError):
            if fallback is not None:
                return uuid5(NAMESPACE_URL, f"ksp-api:{name}:{fallback}")
            raise ApplicationError("API_INVALID_UUID", f"{name} must be a UUID.")

    @classmethod
    def _optional_uuid(cls, value: Any) -> UUID | None:
        return None if value in (None, "") else cls._uuid(value, "uuid")

    @staticmethod
    def _datetime(value: str) -> datetime:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    @staticmethod
    def _status_for(code: str) -> int:
        if code in {"AUTHENTICATION_REQUIRED", "AUTH_INVALID_TOKEN", "AUTH_INVALID_CLAIMS"}:
            return 401
        if code.endswith("FORBIDDEN") or code in {"API_TOOL_ROUTE_FORBIDDEN", "UPLOAD_TYPE_FORBIDDEN"}:
            return 403
        if code in {"INVESTIGATION_NOT_FOUND", "RUN_NOT_FOUND", "API_NOT_FOUND"}:
            return 404
        if code in {"CHECKPOINT_VERSION_CONFLICT", "CHECKPOINT_VERSION_INVALID"}:
            return 409
        if code in {"RUNNER_UNAVAILABLE", "FAST_PATH_UNAVAILABLE"}:
            return 503
        if code == "UPLOAD_TOO_LARGE":
            return 413
        if code.startswith("UPLOAD_") or code.startswith("API_"):
            return 400
        return 400


__all__ = ["ApiApplication", "RunRecord", "RunStore", "RunnerProtocol"]
