"""LiteLLM-compatible model routing boundary with no implicit provider calls."""

from __future__ import annotations

from typing import AsyncIterator

from src.shared.config import Settings
from src.shared.errors import AdapterUnavailableError, ApplicationError
from src.shared.ports import ModelBackend, ModelRequest, ModelResponse, StreamChunk


class LiteLLMRouter:
    """Provider-neutral model router.

    LiteLLM is injected as a backend in a later orchestration phase. Until then,
    ``LLM_ENABLED`` remains false and no provider/network call can occur.
    """

    def __init__(self, settings: Settings, backend: ModelBackend | None = None) -> None:
        self.settings = settings
        self.backend = backend

    @property
    def model_chain(self) -> tuple[str, str, str, str]:
        return self.settings.model_chain

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self._validate_request(request)
        self._require_backend()
        attempted: list[str] = []
        for model in self.model_chain:
            attempted.append(model)
            try:
                return await self.backend.complete(model, request)
            except Exception:
                # Provider exception details may contain request content or secrets;
                # keep them out of the public error envelope and try the next model.
                continue
        raise AdapterUnavailableError(
            "LLM_ALL_PROVIDERS_FAILED",
            "All configured LLM providers failed without exposing provider details.",
            details={"attempted_models": attempted},
        )

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        self._validate_request(request)
        self._require_backend()
        async for chunk in self.backend.stream(self.model_chain[0], request):
            yield chunk

    def _require_backend(self) -> None:
        if not self.settings.llm_enabled:
            raise AdapterUnavailableError(
                "LLM_DISABLED",
                "LLM access is disabled by configuration.",
                details={"model_chain": list(self.model_chain)},
            )
        if self.backend is None:
            raise AdapterUnavailableError(
                "LLM_BACKEND_UNCONFIGURED",
                "No validated LiteLLM backend has been injected.",
                details={"model_chain": list(self.model_chain)},
            )

    @staticmethod
    def _validate_request(request: ModelRequest) -> None:
        if not request.messages:
            raise ApplicationError("LLM_EMPTY_MESSAGES", "At least one model message is required.")
        if not 1 <= request.max_tokens <= 4096:
            raise ApplicationError("LLM_INVALID_MAX_TOKENS", "max_tokens must be between 1 and 4096.")
        if not 0.0 <= request.temperature <= 1.0:
            raise ApplicationError("LLM_INVALID_TEMPERATURE", "temperature must be between 0 and 1.")
