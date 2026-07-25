"""Environment-driven settings with explicit security and deployment validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import urlparse

from .errors import ConfigurationError

_ALLOWED_ENVIRONMENTS = frozenset({"local", "test", "catalyst", "production"})
_ALLOWED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_MODEL_CHAIN = (
    "groq/llama-3.3-70b-versatile",
    "gemini/gemini-2.5-flash",
    "mistral/mistral-small-latest",
    "openrouter/meta-llama/llama-3.1-8b-instruct:free",
)
_SECRET_FIELDS = frozenset(
    {
        "neo4j_password",
        "groq_api_key",
        "gemini_api_key",
        "mistral_api_key",
        "openrouter_api_key",
    }
)


class SettingsError(ConfigurationError):
    """Raised when environment configuration cannot safely initialize."""


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings; secret fields never appear in repr output."""

    app_env: str = "local"
    log_level: str = "INFO"
    catalyst_project_id: str | None = None
    catalyst_app_id: str | None = None
    catalyst_environment: str = "development"
    catalyst_api_base_url: str | None = None
    frontend_origin: str | None = None
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str | None = None
    neo4j_password: str | None = field(default=None, repr=False)
    neo4j_bolt_port: int = 7687
    neo4j_http_port: int = 7474
    data_store_id: str | None = None
    data_store_enabled: bool = False
    cache_enabled: bool = False
    stratus_enabled: bool = False
    catalyst_auth_enabled: bool = False
    groq_api_key: str | None = field(default=None, repr=False)
    gemini_api_key: str | None = field(default=None, repr=False)
    mistral_api_key: str | None = field(default=None, repr=False)
    openrouter_api_key: str | None = field(default=None, repr=False)
    primary_model: str = _MODEL_CHAIN[0]
    reasoning_model: str = _MODEL_CHAIN[1]
    fallback_model: str = _MODEL_CHAIN[2]
    emergency_fallback_model: str = _MODEL_CHAIN[3]
    embedding_model: str = "AlpEge/bge-m3-onnx-int8"
    reranker_model: str = "Sophia-AI/bge-reranker-v2-m3-onnx"
    embedding_dimensions: int = 1024
    api_timeout_seconds: int = 30
    signal_timeout_seconds: int = 60
    job_timeout_seconds: int = 300

    @property
    def model_chain(self) -> tuple[str, str, str, str]:
        return (
            self.primary_model,
            self.reasoning_model,
            self.fallback_model,
            self.emergency_fallback_model,
        )

    @property
    def is_production_like(self) -> bool:
        return self.app_env in {"catalyst", "production"}

    def redacted(self) -> dict[str, object]:
        """Return diagnostics-safe settings without secret values."""

        values = self.__dict__.copy()
        for field_name in _SECRET_FIELDS:
            if field_name in values:
                values[field_name] = "[REDACTED]" if values[field_name] else None
        values["model_chain"] = self.model_chain
        return values

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        source = dict(os.environ if environ is None else environ)
        app_env = _read_choice(source, "APP_ENV", "local", _ALLOWED_ENVIRONMENTS)
        settings = cls(
            app_env=app_env,
            log_level=_read_choice(source, "LOG_LEVEL", "INFO", _ALLOWED_LOG_LEVELS),
            catalyst_project_id=_optional(source, "CATALYST_PROJECT_ID"),
            catalyst_app_id=_optional(source, "CATALYST_APP_ID"),
            catalyst_environment=source.get("CATALYST_ENVIRONMENT", "development"),
            catalyst_api_base_url=_optional(source, "CATALYST_API_BASE_URL"),
            frontend_origin=_optional(source, "FRONTEND_ORIGIN"),
            neo4j_uri=source.get("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=_optional(source, "NEO4J_USER"),
            neo4j_password=_optional(source, "NEO4J_PASSWORD"),
            neo4j_bolt_port=_read_int(source, "NEO4J_BOLT_PORT", 7687, 1, 65535),
            neo4j_http_port=_read_int(source, "NEO4J_HTTP_PORT", 7474, 1, 65535),
            data_store_id=_optional(source, "CATALYST_DATA_STORE_ID"),
            data_store_enabled=_read_bool(source, "CATALYST_DATA_STORE_ENABLED", False),
            cache_enabled=_read_bool(source, "CATALYST_CACHE_ENABLED", False),
            stratus_enabled=_read_bool(source, "CATALYST_STRATUS_ENABLED", False),
            catalyst_auth_enabled=_read_bool(source, "CATALYST_AUTH_ENABLED", False),
            groq_api_key=_optional(source, "GROQ_API_KEY"),
            gemini_api_key=_optional(source, "GEMINI_API_KEY"),
            mistral_api_key=_optional(source, "MISTRAL_API_KEY"),
            openrouter_api_key=_optional(source, "OPENROUTER_API_KEY"),
            primary_model=source.get("PRIMARY_MODEL", _MODEL_CHAIN[0]),
            reasoning_model=source.get("REASONING_MODEL", _MODEL_CHAIN[1]),
            fallback_model=source.get("FALLBACK_MODEL", _MODEL_CHAIN[2]),
            emergency_fallback_model=source.get("EMERGENCY_FALLBACK_MODEL", _MODEL_CHAIN[3]),
            embedding_model=source.get("EMBEDDING_MODEL", "AlpEge/bge-m3-onnx-int8"),
            reranker_model=source.get("RERANKER_MODEL", "Sophia-AI/bge-reranker-v2-m3-onnx"),
            embedding_dimensions=_read_int(source, "EMBEDDING_DIMENSIONS", 1024, 1, 4096),
            api_timeout_seconds=_read_int(source, "API_TIMEOUT_SECONDS", 30, 1, 300),
            signal_timeout_seconds=_read_int(source, "SIGNAL_TIMEOUT_SECONDS", 60, 1, 600),
            job_timeout_seconds=_read_int(source, "JOB_TIMEOUT_SECONDS", 300, 1, 1800),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.neo4j_bolt_port != 7687:
            raise SettingsError(
                "CONFIG_INVALID_PORT",
                "NEO4J_BOLT_PORT must remain 7687 for the locked AppSail topology.",
            )
        if self.neo4j_http_port != 7474:
            raise SettingsError(
                "CONFIG_INVALID_PORT",
                "NEO4J_HTTP_PORT must remain 7474 for the locked Neo4j topology.",
            )
        parsed = urlparse(self.neo4j_uri)
        if parsed.scheme not in {"bolt", "bolt+s", "bolt+ssc", "neo4j", "neo4j+s", "neo4j+ssc"}:
            raise SettingsError(
                "CONFIG_INVALID_URI",
                "NEO4J_URI must use a Neo4j Bolt-compatible URI scheme.",
            )
        if self.catalyst_api_base_url:
            api_url = urlparse(self.catalyst_api_base_url)
            if api_url.scheme != "https" and self.is_production_like:
                raise SettingsError(
                    "CONFIG_INSECURE_URL",
                    "CATALYST_API_BASE_URL must use HTTPS in Catalyst or production environments.",
                )
        if self.frontend_origin and self.is_production_like:
            origin_url = urlparse(self.frontend_origin)
            if origin_url.scheme != "https":
                raise SettingsError(
                    "CONFIG_INSECURE_ORIGIN",
                    "FRONTEND_ORIGIN must use HTTPS in Catalyst or production environments.",
                )
        if self.is_production_like:
            missing = [
                name
                for name, value in (
                    ("CATALYST_PROJECT_ID", self.catalyst_project_id),
                    ("CATALYST_APP_ID", self.catalyst_app_id),
                    ("NEO4J_USER", self.neo4j_user),
                    ("NEO4J_PASSWORD", self.neo4j_password),
                )
                if not value
            ]
            if missing:
                raise SettingsError(
                    "CONFIG_MISSING_REQUIRED",
                    "Required deployment configuration is missing.",
                    details={"variables": missing},
                )


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Load and validate settings without logging or printing secret values."""

    return Settings.from_env(environ)


def _optional(source: Mapping[str, str], key: str) -> str | None:
    value = source.get(key)
    return value.strip() if value and value.strip() else None


def _read_choice(source: Mapping[str, str], key: str, default: str, allowed: frozenset[str]) -> str:
    value = source.get(key, default).strip()
    if value not in allowed:
        raise SettingsError(
            "CONFIG_INVALID_VALUE",
            f"{key} has an unsupported value.",
            details={"variable": key, "allowed": sorted(allowed)},
        )
    return value


def _read_int(source: Mapping[str, str], key: str, default: int, minimum: int, maximum: int) -> int:
    raw = source.get(key, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise SettingsError(
            "CONFIG_INVALID_INTEGER",
            f"{key} must be an integer.",
            details={"variable": key},
        ) from exc
    if not minimum <= value <= maximum:
        raise SettingsError(
            "CONFIG_OUT_OF_RANGE",
            f"{key} is outside its allowed range.",
            details={"variable": key, "minimum": minimum, "maximum": maximum},
        )
    return value


def _read_bool(source: Mapping[str, str], key: str, default: bool) -> bool:
    raw = source.get(key)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(
        "CONFIG_INVALID_BOOLEAN",
        f"{key} must be a boolean.",
        details={"variable": key},
    )
