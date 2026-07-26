"""Application auth-claim adapter; external Catalyst/Hexel policy remains authoritative."""

from __future__ import annotations

from dataclasses import dataclass

from src.registry.tools import AuthorizationContext


@dataclass(frozen=True)
class AuthClaims:
    officer_id: str
    role: str
    scopes: frozenset[str]
    station_id: str | None = None
    district_id: str | None = None
    investigation_id: str | None = None

    def to_context(self) -> AuthorizationContext:
        scoped = set(self.scopes)
        if self.station_id:
            scoped.add(f"station:{self.station_id}")
        if self.district_id:
            scoped.add(f"district:{self.district_id}")
        return AuthorizationContext(self.officer_id, self.role, frozenset(scoped), investigation_id=self.investigation_id)


def claims_from_mapping(claims: dict[str, object]) -> AuthClaims:
    return AuthClaims(
        officer_id=str(claims.get("officer_id", "")), role=str(claims.get("role", "")),
        scopes=frozenset(str(value) for value in claims.get("scopes", ())),
        station_id=str(claims["station_id"]) if claims.get("station_id") else None,
        district_id=str(claims["district_id"]) if claims.get("district_id") else None,
        investigation_id=str(claims["investigation_id"]) if claims.get("investigation_id") else None,
    )


__all__ = ["AuthClaims", "claims_from_mapping"]
