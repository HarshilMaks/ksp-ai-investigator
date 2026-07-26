"""Catalyst-compatible checkpoint ports and a durable local adapter for P09."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol
from uuid import UUID

from src.adapters.catalyst.repositories import CatalystRepositorySet
from src.domain.investigation_state import InvestigationState, InvestigationStateError
from src.shared.ports import DataStorePort


class CheckpointError(InvestigationStateError):
    """Checkpoint read/write or optimistic-concurrency failure."""


class CheckpointConflict(CheckpointError):
    """A checkpoint write was based on a stale state version."""


class CheckpointStore(Protocol):
    async def save(
        self,
        state: InvestigationState,
        *,
        expected_version: int | None = None,
        audit_context: Mapping[str, Any] | None = None,
    ) -> InvestigationState: ...

    async def load(self, investigation_id: UUID) -> InvestigationState | None: ...


@dataclass(frozen=True)
class Checkpoint:
    investigation_id: UUID
    version: int
    state: dict[str, Any]


class LocalCheckpointStore:
    """Atomic JSON checkpoint store that survives local service instances."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _latest_path(self, investigation_id: UUID) -> Path:
        return self.root / f"{investigation_id}.latest.json"

    def _version_path(self, investigation_id: UUID, version: int) -> Path:
        return self.root / f"{investigation_id}.v{version}.json"

    async def save(
        self,
        state: InvestigationState,
        *,
        expected_version: int | None = None,
        audit_context: Mapping[str, Any] | None = None,
    ) -> InvestigationState:
        async with self._lock:
            latest = await self._read_latest(state.investigation_id)
            current_version = None if latest is None else int(latest["version"])
            if expected_version != current_version:
                raise CheckpointConflict(
                    "CHECKPOINT_VERSION_CONFLICT",
                    "Checkpoint write is based on a stale investigation version.",
                    details={"expected_version": expected_version, "current_version": current_version},
                )
            expected_next = 1 if current_version is None else current_version + 1
            if state.version != expected_next:
                raise CheckpointConflict(
                    "CHECKPOINT_VERSION_INVALID",
                    "Checkpoint state version must be the next version.",
                    details={"expected_version": expected_next, "state_version": state.version},
                )
            checkpoint_id = f"{state.investigation_id}:v{state.version}"
            persisted_state = state.with_version(state.version, checkpoint_id=checkpoint_id)
            payload = {"investigation_id": str(state.investigation_id), "version": state.version, "state": persisted_state.to_record()}
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            version_path = self._version_path(state.investigation_id, state.version)
            latest_path = self._latest_path(state.investigation_id)
            await asyncio.to_thread(self._atomic_write, version_path, encoded)
            await asyncio.to_thread(self._atomic_write, latest_path, encoded)
            return persisted_state

    async def load(self, investigation_id: UUID) -> InvestigationState | None:
        async with self._lock:
            payload = await self._read_latest(investigation_id)
        if payload is None:
            return None
        try:
            return InvestigationState.from_record(payload["state"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CheckpointError("CHECKPOINT_CORRUPT", "The persisted investigation checkpoint is invalid.") from exc

    async def versions(self, investigation_id: UUID) -> tuple[int, ...]:
        async with self._lock:
            paths = sorted(self.root.glob(f"{investigation_id}.v*.json"))
        versions: list[int] = []
        for path in paths:
            try:
                versions.append(int(path.stem.rsplit(".v", 1)[1]))
            except (IndexError, ValueError):
                continue
        return tuple(versions)

    async def _read_latest(self, investigation_id: UUID) -> dict[str, Any] | None:
        path = self._latest_path(investigation_id)
        if not path.is_file():
            return None
        try:
            return json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CheckpointError("CHECKPOINT_READ_FAILED", "The investigation checkpoint could not be read.") from exc

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)


class CatalystCheckpointStore:
    """Catalyst Data Store implementation of the same P09 checkpoint contract."""

    resource = "investigation_checkpoints"

    def __init__(
        self,
        data_store: DataStorePort,
        normalized: CatalystRepositorySet | None = None,
    ) -> None:
        self.data_store = data_store
        self.normalized = normalized or CatalystRepositorySet.from_data_store(data_store)

    async def save(
        self,
        state: InvestigationState,
        *,
        expected_version: int | None = None,
        audit_context: Mapping[str, Any] | None = None,
    ) -> InvestigationState:
        latest = await self.data_store.get(self.resource, str(state.investigation_id))
        current_version = None if latest is None else int(latest.get("version", 0))
        if expected_version != current_version:
            raise CheckpointConflict(
                "CHECKPOINT_VERSION_CONFLICT",
                "Checkpoint write is based on a stale investigation version.",
                details={"expected_version": expected_version, "current_version": current_version},
            )
        expected_next = 1 if current_version is None else current_version + 1
        if state.version != expected_next:
            raise CheckpointConflict(
                "CHECKPOINT_VERSION_INVALID",
                "Checkpoint state version must be the next version.",
                details={"expected_version": expected_next, "state_version": state.version},
            )
        persisted_state = state.with_version(state.version, checkpoint_id=f"{state.investigation_id}:v{state.version}")
        await self.data_store.put(
            self.resource,
            str(state.investigation_id),
            {"investigation_id": str(state.investigation_id), "version": state.version, "state": persisted_state.to_record()},
        )
        role = str((audit_context or {}).get("user_role", "APPLICATION"))
        await self.normalized.persist_investigation_state(persisted_state, user_role=role)
        return persisted_state

    async def load(self, investigation_id: UUID) -> InvestigationState | None:
        payload = await self.data_store.get(self.resource, str(investigation_id))
        if payload is None:
            return None
        try:
            return InvestigationState.from_record(payload["state"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CheckpointError("CHECKPOINT_CORRUPT", "The Catalyst investigation checkpoint is invalid.") from exc


__all__ = ["CatalystCheckpointStore", "Checkpoint", "CheckpointConflict", "CheckpointError", "CheckpointStore", "LocalCheckpointStore"]
