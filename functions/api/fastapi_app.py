"""Catalyst AppSail FastAPI entry-point adapter.

Deployment composition injects the fully configured ApiApplication; this module
never constructs credentials or external clients implicitly.
"""

from fastapi import FastAPI

from src.api import ApiApplication, create_fastapi_app


def create_app(application: ApiApplication) -> FastAPI:
    return create_fastapi_app(application)


__all__ = ["create_app"]
