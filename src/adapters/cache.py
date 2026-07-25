"""Cache adapter selection; external Catalyst Cache is never implicit."""

from __future__ import annotations

from typing import Any

from src.adapters.catalyst.local import LocalCache
from src.adapters.catalyst.sdk import CatalystCacheAdapter
from src.shared.config import Settings
from src.shared.ports import ExternalTransport


def build_cache(settings: Settings, transport: ExternalTransport | None = None) -> LocalCache | CatalystCacheAdapter:
    """Return local cache by default; require explicit configuration for Catalyst."""

    if settings.catalyst_external_enabled and settings.cache_enabled:
        return CatalystCacheAdapter(settings, transport)
    return LocalCache()


__all__ = ["CatalystCacheAdapter", "LocalCache", "build_cache"]
