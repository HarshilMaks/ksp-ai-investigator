"""Function-level configuration bridge with no adapter or business logic."""

from src.shared.config import Settings, load_settings

__all__ = ["Settings", "load_settings"]
