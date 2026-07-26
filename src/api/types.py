"""Typed request/response contracts for the P10 application API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import parse_qs, urlsplit


@dataclass(frozen=True)
class ApiRequest:
    method: str
    path: str
    headers: Mapping[str, str] = field(default_factory=dict)
    body: bytes = b""

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", self.method.upper())
        object.__setattr__(self, "headers", {str(key).lower(): str(value) for key, value in self.headers.items()})

    @property
    def route(self) -> str:
        return urlsplit(self.path).path

    @property
    def query(self) -> dict[str, list[str]]:
        return parse_qs(urlsplit(self.path).query)

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "")


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: bytes = b""
    headers: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def json(cls, status: int, payload: object, *, request_id: str, extra_headers: Mapping[str, str] | None = None) -> "ApiResponse":
        import json

        headers = {"content-type": "application/json; charset=utf-8", "x-request-id": request_id}
        if extra_headers:
            headers.update(extra_headers)
        return cls(status=status, body=json.dumps(payload, sort_keys=True, default=str).encode("utf-8"), headers=headers)


@dataclass(frozen=True)
class AuthPrincipal:
    officer_id: str
    role: str
    scopes: frozenset[str]
    investigation_id: str | None = None


__all__ = ["ApiRequest", "ApiResponse", "AuthPrincipal"]
