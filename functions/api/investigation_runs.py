"""Investigation run lifecycle entry point; business logic remains in src.api."""

from src.api.application import ApiApplication
from src.api.types import ApiRequest, ApiResponse


async def handle(request: ApiRequest, application: ApiApplication) -> ApiResponse:
    return await application.handle(request)
