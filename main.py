"""KSP InvestigateAI FastAPI application facade.

Run locally with:

    uv run uvicorn main:app --host 0.0.0.0 --port 8000

The facade composes infrastructure and exposes ``app``. Business routing and
application behavior remain in ``src.api``; Catalyst Auth and deployed storage
are injected at the deployment boundary when those services are available.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from src.adapters.catalyst import CatalystDataStoreAdapter
from src.adapters.catalyst.repositories import CatalystRepositorySet
from src.api import ApiApplication, ApiAuthenticator, StaticAuthVerifier, create_fastapi_app
from src.services.checkpoints import CatalystCheckpointStore, LocalCheckpointStore
from src.services.investigations import InvestigationService
from src.shared.config import Settings, load_settings
from src.shared.ports import ExternalTransport


def build_api_application(
    *,
    settings: Settings | None = None,
    authenticator: ApiAuthenticator | None = None,
    checkpoint_dir: str | Path | None = None,
    catalyst_transport: ExternalTransport | None = None,
) -> ApiApplication:
    """Compose the local application core without creating external clients.

    The default verifier intentionally has no accepted tokens, so importing the
    local facade cannot create an insecure development credential. Deployment
    code should inject an ``ApiAuthenticator`` backed by Catalyst Auth.
    """

    runtime_settings = settings or load_settings()
    verifier = authenticator or ApiAuthenticator(StaticAuthVerifier({}))
    root = Path(checkpoint_dir or os.environ.get("KSP_CHECKPOINT_DIR", ".local/checkpoints"))
    if runtime_settings.app_env == "catalyst":
        data_store = CatalystDataStoreAdapter(runtime_settings, catalyst_transport)
        repositories = CatalystRepositorySet.from_data_store(data_store)
        checkpoints = CatalystCheckpointStore(data_store, normalized=repositories)
    else:
        checkpoints = LocalCheckpointStore(root)
    return ApiApplication(
        InvestigationService(checkpoints),
        verifier,
        cors_origin=runtime_settings.frontend_origin or "http://localhost:3000",
    )


def create_app(
    application: ApiApplication | None = None,
    *,
    settings: Settings | None = None,
    authenticator: ApiAuthenticator | None = None,
    checkpoint_dir: str | Path | None = None,
    catalyst_transport: ExternalTransport | None = None,
) -> FastAPI:
    """Create the FastAPI app, optionally with an injected application core."""

    core = application or build_api_application(
        settings=settings,
        authenticator=authenticator,
        checkpoint_dir=checkpoint_dir,
        catalyst_transport=catalyst_transport,
    )
    return create_fastapi_app(core)


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
    )


__all__ = ["app", "build_api_application", "create_app"]
