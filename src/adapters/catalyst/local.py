"""Local deterministic adapters for tests and offline development."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from src.shared.errors import ApplicationError
from src.shared.ports import DataStorePort, EventPort, ObjectStorePort


class LocalDataStore(DataStorePort):
    """In-memory structured store with exact filter semantics for local tests."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def get(self, resource: str, key: str) -> dict[str, Any] | None:
        async with self._lock:
            value = self._records.get(resource, {}).get(key)
            return dict(value) if value is not None else None

    async def put(self, resource: str, key: str, value: dict[str, Any]) -> None:
        async with self._lock:
            self._records.setdefault(resource, {})[key] = dict(value)

    async def delete(self, resource: str, key: str) -> None:
        async with self._lock:
            self._records.get(resource, {}).pop(key, None)

    async def query(self, resource: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        async with self._lock:
            records = list(self._records.get(resource, {}).values())
        return [
            dict(record)
            for record in records
            if all(record.get(key) == value for key, value in filters.items())
        ]


class LocalCache:
    """In-memory cache with optional TTL and no external network behavior."""

    def __init__(self) -> None:
        self._values: dict[str, tuple[float | None, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            item = self._values.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at is not None and expires_at <= time.monotonic():
                self._values.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> None:
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ApplicationError("CACHE_INVALID_TTL", "Cache TTL must be positive.")
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds is not None else None
        async with self._lock:
            self._values[key] = (expires_at, value)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._values.pop(key, None)


class LocalObjectStore(ObjectStorePort):
    """File-backed object store used only for local deterministic tests."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ApplicationError("OBJECT_INVALID_KEY", "Object key escapes the local store.")
        return candidate

    async def put(self, key: str, content: bytes, *, content_type: str) -> None:
        if not content_type:
            raise ApplicationError("OBJECT_INVALID_CONTENT_TYPE", "Content type is required.")
        path = self._path_for(key)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, content)

    async def get(self, key: str) -> bytes | None:
        path = self._path_for(key)
        if not path.is_file():
            return None
        return await asyncio.to_thread(path.read_bytes)

    async def delete(self, key: str) -> None:
        path = self._path_for(key)
        if path.exists():
            await asyncio.to_thread(path.unlink)


class LocalEventBus(EventPort):
    """In-memory event collector for Signals/Cron/Circuits contract tests."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, topic: str, payload: dict[str, Any]) -> str:
        event_id = f"local-{len(self.events) + 1:08d}"
        self.events.append((topic, dict(payload)))
        return event_id


class LocalAuth:
    """Explicit local token map; never a production authentication mechanism."""

    def __init__(self, tokens: dict[str, dict[str, Any]] | None = None) -> None:
        self._tokens = tokens or {}

    async def verify(self, token: str) -> dict[str, Any]:
        subject = self._tokens.get(token)
        if subject is None:
            raise ApplicationError("AUTH_INVALID_TOKEN", "Authentication token is invalid.")
        return dict(subject)
