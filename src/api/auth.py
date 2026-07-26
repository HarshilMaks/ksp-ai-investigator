"""Cookie/bearer authentication boundary for REST and SSE requests."""

from __future__ import annotations

import inspect
from http.cookies import SimpleCookie
from typing import Any, Awaitable, Mapping, Protocol

from src.registry.tools import AuthorizationContext
from src.shared.errors import ApplicationError

from .types import AuthPrincipal


class AuthVerifier(Protocol):
    def verify(self, token: str) -> Mapping[str, Any] | Awaitable[Mapping[str, Any]]: ...


class StaticAuthVerifier:
    """Deterministic local verifier for tests and offline API smoke checks."""

    def __init__(self, claims: Mapping[str, Mapping[str, Any]]) -> None:
        self.claims = {str(token): dict(value) for token, value in claims.items()}

    def verify(self, token: str) -> Mapping[str, Any]:
        claims = self.claims.get(token)
        if claims is None:
            raise ApplicationError("AUTH_INVALID_TOKEN", "Authentication token is invalid.")
        return claims


class ApiAuthenticator:
    """Accept bearer tokens and cookie tokens without assuming native EventSource headers."""

    def __init__(self, verifier: AuthVerifier, *, cookie_names: tuple[str, ...] = ("catalyst_auth", "session")) -> None:
        self.verifier = verifier
        self.cookie_names = cookie_names

    async def authenticate(self, headers: Mapping[str, str]) -> AuthorizationContext:
        normalized = {str(key).lower(): value for key, value in headers.items()}
        token = self._token(normalized)
        if not token:
            raise ApplicationError("AUTHENTICATION_REQUIRED", "A bearer token or authenticated session cookie is required.")
        claims = self.verifier.verify(token)
        if inspect.isawaitable(claims):
            claims = await claims
        officer_id = str(claims.get("officer_id") or claims.get("sub") or "").strip()
        role = str(claims.get("role") or "").strip()
        if not officer_id or not role:
            raise ApplicationError("AUTH_INVALID_CLAIMS", "Authenticated claims must include officer_id and role.")
        raw_scopes = claims.get("scopes", ())
        if isinstance(raw_scopes, str):
            scopes = frozenset(value for value in raw_scopes.split() if value)
        else:
            scopes = frozenset(str(value) for value in raw_scopes)
        return AuthorizationContext(
            officer_id=officer_id,
            role=role,
            scopes=scopes,
            allowed_tool_ids=frozenset(str(value) for value in claims.get("allowed_tool_ids", ())) or None,
            investigation_id=str(claims["investigation_id"]) if claims.get("investigation_id") else None,
        )

    def _token(self, headers: Mapping[str, str]) -> str | None:
        authorization = headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            return authorization[7:].strip() or None
        cookie_header = headers.get("cookie", "")
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        for name in self.cookie_names:
            morsel = cookie.get(name)
            if morsel and morsel.value:
                return morsel.value
        return None


__all__ = ["ApiAuthenticator", "AuthVerifier", "StaticAuthVerifier"]
