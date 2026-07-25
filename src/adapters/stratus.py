"""Stratus object-store adapter selection."""

from __future__ import annotations

from pathlib import Path

from src.adapters.catalyst.local import LocalObjectStore
from src.adapters.catalyst.sdk import CatalystStratusAdapter
from src.shared.config import Settings
from src.shared.ports import ExternalTransport


def build_object_store(
    settings: Settings,
    local_root: str | Path,
    transport: ExternalTransport | None = None,
) -> LocalObjectStore | CatalystStratusAdapter:
    """Use a local file store until a validated Stratus transport is injected."""

    if settings.catalyst_external_enabled and settings.stratus_enabled:
        return CatalystStratusAdapter(settings, transport)
    return LocalObjectStore(local_root)


__all__ = ["CatalystStratusAdapter", "LocalObjectStore", "build_object_store"]
