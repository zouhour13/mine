"""
Application settings.

All configuration comes from environment variables (or a .env file).
This module is intentionally kept to settings/values only.
Client construction belongs in core/dependencies.py.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── GitHub ────────────────────────────────────────────────────────────────
    # Optional: public repos work without a token.
    # Provide a PAT to increase rate limits from 60 to 5 000 req/hr.
    github_token: str | None = None

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_provider: str = "gemini"
    gemini_api_key: str = ""

    # ── Database ──────────────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_service_key: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    # ── Analysis limits ───────────────────────────────────────────────────────
    max_readme_chars: int = 2_000
    max_files_to_fetch: int = 5
    max_file_chars: int = 800
    max_concepts: int = 20
    min_concepts: int = 5


settings = Settings()
