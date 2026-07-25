"""Neo4j Bolt boundary without importing the driver before P03 validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.shared.config import Settings
from src.shared.errors import AdapterUnavailableError, ApplicationError


@dataclass(frozen=True)
class Neo4jConnectionInfo:
    uri: str
    user: str | None
    bolt_port: int = 7687
    http_port: int = 7474


class Neo4jClient:
    """Validated connection boundary for Neo4j 5 Community on AppSail.

    The actual neo4j-driver dependency and connection pool are intentionally deferred
    until the graph phase. This boundary prevents callers from constructing ad hoc
    connection strings or bypassing the locked ports.
    """

    def __init__(self, settings: Settings, driver: Any | None = None) -> None:
        self.settings = settings
        self.connection = Neo4jConnectionInfo(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            bolt_port=settings.neo4j_bolt_port,
            http_port=settings.neo4j_http_port,
        )
        self._driver = driver
        if self.connection.bolt_port != 7687 or self.connection.http_port != 7474:
            raise ApplicationError(
                "NEO4J_INVALID_PORTS",
                "Neo4j adapter ports do not match the locked AppSail topology.",
            )

    @classmethod
    def from_settings(cls, settings: Settings, driver: Any | None = None) -> "Neo4jClient":
        return cls(settings, driver)

    @property
    def enabled(self) -> bool:
        return self.settings.neo4j_enabled

    async def read(self, cypher: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        self._require_driver()
        result = await self._driver.read(cypher, dict(params or {}))
        return list(result)

    async def write(self, cypher: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        self._require_driver()
        result = await self._driver.write(cypher, dict(params or {}))
        return list(result)

    def _require_driver(self) -> None:
        if not self.settings.neo4j_enabled:
            raise AdapterUnavailableError(
                "NEO4J_DISABLED",
                "Neo4j access is disabled by configuration.",
                details={"uri": self.connection.uri, "bolt_port": self.connection.bolt_port},
            )
        if self._driver is None:
            raise AdapterUnavailableError(
                "NEO4J_DRIVER_UNCONFIGURED",
                "No validated Neo4j driver has been injected.",
                details={"uri": self.connection.uri, "bolt_port": self.connection.bolt_port},
            )
