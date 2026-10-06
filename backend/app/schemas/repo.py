"""Schemas for repository API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl, field_validator


RepoStatus = Literal["pending", "analyzing", "completed", "failed"]


class RepoCreate(BaseModel):
    """Request body for POST /api/v1/repos."""

    github_url: str

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if v.endswith(".git"):
            v = v[:-4]
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must include http:// or https://")
        return v


class RepoRead(BaseModel):
    """Response schema for a single repository."""

    id: str
    github_url: str
    owner: str
    name: str
    description: str | None = None
    primary_language: str | None = None
    topics: list[str] = []
    status: RepoStatus
    error_message: str | None = None
    created_at: datetime
    analyzed_at: datetime | None = None


class RepoContext(BaseModel):
    """Internal model — assembled context sent to the LLM.  Never returned via API."""

    owner: str
    name: str
    description: str | None
    primary_language: str | None
    language_breakdown: dict[str, int]
    topics: list[str]
    readme_excerpt: str | None
    top_level_tree: list[str]
    key_files: dict[str, str]  # filename → content excerpt
