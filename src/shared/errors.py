"""Safe application error envelopes and request identifiers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


def new_request_id() -> str:
    """Create a correlation ID without exposing user or secret data."""

    return str(uuid4())


@dataclass(frozen=True)
class ErrorResponse:
    """Stable external error shape for future REST and SSE adapters."""

    code: str
    message: str
    request_id: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "request_id": self.request_id,
            }
        }


class ApplicationError(Exception):
    """Expected, safe-to-return application failure."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.request_id = request_id or new_request_id()
        self.details = details or {}

    def to_response(self) -> ErrorResponse:
        return ErrorResponse(
            code=self.code,
            message=self.message,
            request_id=self.request_id,
            details=self.details,
        )

class ConfigurationError(ApplicationError, ValueError):
    """Configuration is missing, malformed, or unsafe for the selected environment."""
