"""Catalyst adapter contracts and disabled-by-default service wrappers."""

from __future__ import annotations

from typing import Any

from src.shared.config import Settings
from src.shared.errors import AdapterUnavailableError
from src.shared.ports import (
    AuthPort,
    CachePort,
    CatalystRequest,
    CatalystResponse,
    DataStorePort,
    EventPort,
    ExternalTransport,
    JsonObject,
    ObjectStorePort,
)
from src.shared.errors import new_request_id


class CatalystServiceAdapter:
    """Common boundary for Catalyst SDK transports.

    No SDK import or network call occurs here. A deployment-specific transport must
    be injected after Catalyst compatibility is validated.
    """

    def __init__(
        self,
        settings: Settings,
        service: str,
        transport: ExternalTransport | None = None,
    ) -> None:
        self.settings = settings
        self.service = service
        self.transport = transport

    async def dispatch(self, operation: str, payload: JsonObject) -> CatalystResponse:
        if not self.settings.catalyst_external_enabled:
            raise AdapterUnavailableError(
                "CATALYST_DISABLED",
                "External Catalyst adapters are disabled by configuration.",
                details={"service": self.service, "operation": operation},
            )
        if self.transport is None:
            raise AdapterUnavailableError(
                "CATALYST_TRANSPORT_UNCONFIGURED",
                "No validated Catalyst transport has been injected.",
                details={"service": self.service},
            )
        request = CatalystRequest(
            service=self.service,
            operation=operation,
            payload=dict(payload),
            request_id=new_request_id(),
        )
        return await self.transport.send(request)


class CatalystDataStoreAdapter(CatalystServiceAdapter, DataStorePort):
    def __init__(self, settings: Settings, transport: ExternalTransport | None = None) -> None:
        super().__init__(settings, "data_store", transport)

    async def get(self, resource: str, key: str) -> JsonObject | None:
        response = await self.dispatch("get", {"resource": resource, "key": key})
        return response.payload.get("value")

    async def put(self, resource: str, key: str, value: JsonObject) -> None:
        await self.dispatch("put", {"resource": resource, "key": key, "value": value})

    async def delete(self, resource: str, key: str) -> None:
        await self.dispatch("delete", {"resource": resource, "key": key})

    async def query(self, resource: str, filters: JsonObject) -> list[JsonObject]:
        response = await self.dispatch("query", {"resource": resource, "filters": filters})
        values = response.payload.get("values", [])
        return list(values) if isinstance(values, list) else []


class CatalystCacheAdapter(CatalystServiceAdapter, CachePort):
    def __init__(self, settings: Settings, transport: ExternalTransport | None = None) -> None:
        super().__init__(settings, "cache", transport)

    async def get(self, key: str) -> Any | None:
        response = await self.dispatch("get", {"key": key})
        return response.payload.get("value")

    async def set(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> None:
        await self.dispatch("set", {"key": key, "value": value, "ttl_seconds": ttl_seconds})

    async def delete(self, key: str) -> None:
        await self.dispatch("delete", {"key": key})


class CatalystStratusAdapter(CatalystServiceAdapter, ObjectStorePort):
    def __init__(self, settings: Settings, transport: ExternalTransport | None = None) -> None:
        super().__init__(settings, "stratus", transport)

    async def put(self, key: str, content: bytes, *, content_type: str) -> None:
        await self.dispatch("put", {"key": key, "content": content.hex(), "content_type": content_type})

    async def get(self, key: str) -> bytes | None:
        response = await self.dispatch("get", {"key": key})
        value = response.payload.get("content_hex")
        return bytes.fromhex(value) if isinstance(value, str) else None

    async def delete(self, key: str) -> None:
        await self.dispatch("delete", {"key": key})


class CatalystEventAdapter(CatalystServiceAdapter, EventPort):
    def __init__(self, settings: Settings, transport: ExternalTransport | None = None) -> None:
        super().__init__(settings, "signals", transport)

    async def publish(self, topic: str, payload: JsonObject) -> str:
        response = await self.dispatch("publish", {"topic": topic, "payload": payload})
        event_id = response.payload.get("event_id")
        return str(event_id) if event_id is not None else ""


class CatalystAuthAdapter(CatalystServiceAdapter, AuthPort):
    def __init__(self, settings: Settings, transport: ExternalTransport | None = None) -> None:
        super().__init__(settings, "auth", transport)

    async def verify(self, token: str) -> JsonObject:
        response = await self.dispatch("verify", {"token": token})
        return dict(response.payload.get("claims", {}))
