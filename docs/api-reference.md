# P10 API Reference

P10 provides a typed, framework-neutral Python API core under `src/api/` and thin Catalyst delegates under `functions/api/`. The root `main.py` is the deployment composition facade and exports `app`; it wires the local checkpoint/authentication defaults and mounts the core through `create_fastapi_app`. The FastAPI adapter in `src/api/fastapi_app.py` owns explicit `/api/v1` route registration, OpenAPI, REST response transport, and SSE streaming. The core does not depend on LocalRunner, HexelRunner, a tool gateway, or a provider SDK.

## Application entry point

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

`main.create_app(...)` and `main.build_api_application(...)` accept injected application/authentication dependencies. The default local facade uses a fail-closed empty static verifier and local checkpoints under `.local/checkpoints`; deployment code must inject Catalyst Auth and authoritative storage boundaries rather than adding credentials to `main.py`.

## Authentication

REST and SSE requests accept either:

- `Authorization: Bearer <token>`
- an authenticated `catalyst_auth` or `session` cookie

The authenticated claims are converted to the existing `AuthorizationContext` with officer ID, role, scopes, and optional investigation scope. Native browser `EventSource` is supported through cookie authentication; bearer-only SSE clients must use a fetch-based stream client.

## Resource routes

```http
POST /api/v1/investigations
GET  /api/v1/investigations/{investigation_id}
POST /api/v1/investigations/{investigation_id}/status
POST /api/v1/investigations/{investigation_id}/evidence
POST /api/v1/investigations/{investigation_id}/notes
POST /api/v1/investigations/{investigation_id}/hypotheses
POST /api/v1/investigations/{investigation_id}/timeline
POST /api/v1/investigations/{investigation_id}/leads
POST /api/v1/investigations/{investigation_id}/graph
```

All mutations delegate to `InvestigationService`, which owns P09 authorization, versioning, checkpointing, synchronization, health recalculation, and audit metadata.

## Capability/run routes

```http
POST /api/v1/investigations/{investigation_id}/query
POST /api/v1/investigations/{investigation_id}/network-analysis
POST /api/v1/investigations/{investigation_id}/profile-offender
POST /api/v1/investigations/{investigation_id}/similar-cases
POST /api/v1/investigations/{investigation_id}/hypothesis
POST /api/v1/investigations/{investigation_id}/generate-report
POST /api/v1/investigations/{investigation_id}/runs
GET  /api/v1/runs/{run_id}/events
```

A typed deterministic `tool_call` in the query request is executed synchronously through the injected P08 `FastPathExecutor`. Complex requests create a run and return a stream URL. The API depends only on the `RunnerProtocol`; when no Runner is configured, the SSE stream emits an explicit `RUNNER_UNAVAILABLE` error event instead of silently invoking a fallback runtime.

T01–T23 are never public routes. Requests under `/api/v1/tools/...` are rejected.

## SSE event contract

Events use `text/event-stream` and the following event names:

```text
plan | tool | evidence | token | citation | error | done
```

Each event contains JSON data and may contain an SSE event ID. A normal injected-run stream includes `plan`, applicable evidence/tool events, and `done`. Degraded runs include `error` followed by `done`.

## Multipart uploads

```http
POST /api/v1/investigations/{investigation_id}/uploads
Content-Type: multipart/form-data; boundary=...
```

The P10 boundary validates multipart framing, filename, allowed content type, and a configurable byte limit. It does not bypass investigation authorization or persist unvalidated content. Supported local contract types are PDF, plain text, WAV/MP3 audio, and JPEG/PNG images.

## Errors and correlation

Errors use the shared envelope:

```json
{
  "error": {
    "code": "API_INVALID_REQUEST",
    "message": "Request is malformed.",
    "details": {},
    "request_id": "..."
  }
}
```

Every response includes `x-request-id`; callers may provide one to correlate an investigation request and its SSE stream.

## Deferred deployment validation

The local API core is exercised directly and through both its ASGI callable and the optional FastAPI adapter. Live Catalyst API Gateway/AppSail deployment, Catalyst Auth, production CORS configuration, and production SSE behavior remain deployment validation items; no live service or performance claim is made by P10.
