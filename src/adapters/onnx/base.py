"""Optional local CPU model boundary; no model assets are downloaded implicitly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class ModelUnavailableError(RuntimeError):
    """Optional model assets/runtime are not available."""


@dataclass(frozen=True)
class ModelStatus:
    name: str
    available: bool
    reason: str
    device: str = "cpu"


class OptionalModel:
    def __init__(self, name: str, asset_path: str | Path | None = None, *, loader: Callable[[Path], Any] | None = None) -> None:
        self.name = name
        self.asset_path = Path(asset_path) if asset_path else None
        self.loader = loader
        self._model: Any | None = None

    @property
    def status(self) -> ModelStatus:
        if self._model is not None:
            return ModelStatus(self.name, True, "loaded", "cpu")
        if self.asset_path is None:
            return ModelStatus(self.name, False, "model asset path is not configured", "cpu")
        if not self.asset_path.exists():
            return ModelStatus(self.name, False, "model asset is absent", "cpu")
        return ModelStatus(self.name, False, "model is available but not loaded", "cpu")

    def load(self) -> Any:
        if self.asset_path is None or not self.asset_path.exists() or self.loader is None:
            raise ModelUnavailableError(f"{self.name} model assets are unavailable")
        self._model = self.loader(self.asset_path)
        return self._model


__all__ = ["ModelStatus", "ModelUnavailableError", "OptionalModel"]
