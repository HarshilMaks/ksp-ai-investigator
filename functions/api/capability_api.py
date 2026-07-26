"""Capability REST entry point; it delegates to the shared API application."""

from src.api.application import ApiApplication
from src.api.types import ApiRequest, ApiResponse


async def handle(request: ApiRequest, application: ApiApplication) -> ApiResponse:
    return await application.handle(request)
