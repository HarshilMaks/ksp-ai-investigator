"""Typed runtime ports shared by local and Catalyst-backed adapters.

The ports deliberately describe capabilities rather than vendor SDK objects. Engines
and orchestration code depend on these contracts; adapter implementations own all
external connectivity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Mapping, Protocol, Sequence

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class CatalystRequest:
    service: str
    operation: str
    payload: JsonObject = field(default_factory=dict)
    request_id: str | None = None


@dataclass(frozen=True)
class CatalystResponse:
    status_code: int
    payload: JsonObject = field(default_factory=dict)
    request_id: str | None = None


@dataclass(frozen=True)
class ModelRequest:
    messages: Sequence[Mapping[str, str]]
    max_tokens: int = 4096
    temperature: float = 0.1


@dataclass(frozen=True)
class ModelResponse:
    model: str
    content: str
    request_id: str
    provider_metadata: JsonObject = field(default_factory=dict)


@dataclass(frozen=True)
class StreamChunk:
    content: str
    model: str
    request_id: str


class DataStorePort(Protocol):
    async def get(self, resource: str, key: str) -> JsonObject | None: ...

    async def put(self, resource: str, key: str, value: JsonObject) -> None: ...

    async def delete(self, resource: str, key: str) -> None: ...

    async def query(self, resource: str, filters: JsonObject) -> list[JsonObject]: ...


class CachePort(Protocol):
    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> None: ...

    async def delete(self, key: str) -> None: ...


class ObjectStorePort(Protocol):
    async def put(self, key: str, content: bytes, *, content_type: str) -> None: ...

    async def get(self, key: str) -> bytes | None: ...

    async def delete(self, key: str) -> None: ...


class EventPort(Protocol):
    async def publish(self, topic: str, payload: JsonObject) -> str: ...


class AuthPort(Protocol):
    async def verify(self, token: str) -> JsonObject: ...


class ExternalTransport(Protocol):
    async def send(self, request: CatalystRequest) -> CatalystResponse: ...


class ModelBackend(Protocol):
    async def complete(self, model: str, request: ModelRequest) -> ModelResponse: ...

    def stream(self, model: str, request: ModelRequest) -> AsyncIterator[StreamChunk]: ...
