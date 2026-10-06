"""
MINE FastAPI application factory.

Registers routers, CORS middleware, and startup/shutdown lifecycle events.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import concepts, repos


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — nothing to initialise yet; DB client is lazily created.
    yield
    # Shutdown — close the HTTP client used by GitHubClient
    from app.core.dependencies import _build_github_client
    try:
        client = _build_github_client()
        await client.aclose()
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="MINE API",
        description="AI-powered interview speaking trainer for software/AI engineers.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_prefix = "/api/v1"
    app.include_router(repos.router, prefix=api_prefix)
    app.include_router(concepts.router, prefix=api_prefix)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
