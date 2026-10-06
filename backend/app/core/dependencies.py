"""
Dependency factories for FastAPI's dependency injection system.

This module constructs and provides:
- GitHubClient
- LLMClient (provider-agnostic)
- Supabase async client

All client construction lives here, not in config.py.
Routes and services receive clients via FastAPI Depends().
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.clients.github_client import GitHubClient
from app.clients.llm.base import LLMClient
from app.clients.llm.gemini_client import GeminiLLMClient
from app.core.config import settings
from app.core.database import get_db  # noqa: F401  (re-exported for convenience)


@lru_cache(maxsize=1)
def _build_github_client() -> GitHubClient:
    """Construct a GitHubClient once.  token is Optional — None is fine."""
    return GitHubClient(token=settings.github_token)


@lru_cache(maxsize=1)
def _build_llm_client() -> LLMClient:
    """Construct the configured LLM provider once."""
    if settings.llm_provider == "gemini":
        return GeminiLLMClient(api_key=settings.gemini_api_key)
    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
        "Supported providers: gemini"
    )


# ── FastAPI dependency callables ──────────────────────────────────────────────


def get_github_client() -> GitHubClient:
    return _build_github_client()


def get_llm_client() -> LLMClient:
    return _build_llm_client()


# Typed dependency aliases for use in route signatures
GitHubClientDep = Annotated[GitHubClient, Depends(get_github_client)]
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
