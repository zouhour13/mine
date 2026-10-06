"""
Supabase database client.

Provides a single async Supabase client instance.
All database interaction goes through this module — never exposed to the frontend.
"""

from __future__ import annotations

from functools import lru_cache

from supabase import AsyncClient, acreate_client

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_supabase_url() -> str:
    return settings.supabase_url


@lru_cache(maxsize=1)
def _get_supabase_key() -> str:
    return settings.supabase_service_key


# Module-level client — created once at first use.
_client: AsyncClient | None = None


async def get_db() -> AsyncClient:
    """Return the shared Supabase async client, creating it on first call."""
    global _client
    if _client is None:
        _client = await acreate_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )
    return _client
