"""
Repository analysis service.

Orchestrates the full analysis pipeline:
  GitHub metadata → README → languages → file tree → key files →
  LLM concept extraction → Pydantic validation → DB persistence

Status transitions: pending → analyzing → completed | failed

IMPORTANT — BackgroundTasks durability note:
FastAPI BackgroundTasks runs in-process with no persistence.
If the server restarts during analysis, the task is lost and the repo
record will remain stuck at 'pending' or 'analyzing' indefinitely.
This is acceptable for the MVP. A durable queue (Celery + Redis) can be
introduced later without changing service or route code.

Async note:
supabase-py AsyncClient: .table() is synchronous (returns a builder),
only .execute() is async. Pattern is:
  resp = await db.table(...).select(...).eq(...).execute()
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from supabase import AsyncClient

from app.clients.github_client import GitHubClient, parse_github_url
from app.clients.llm.base import LLMClient
from app.core.config import settings
from app.core.exceptions import (
    DatabaseError,
    InvalidGitHubURLError,
    MINEError,
)
from app.schemas.concept import ConceptRead
from app.schemas.repo import RepoContext, RepoRead
from app.services.concept_service import bulk_insert_concepts, get_concepts_for_repo


# ── Repo DB helpers ───────────────────────────────────────────────────────────


async def _get_repo_by_url(db: AsyncClient, github_url: str) -> dict | None:
    resp = await (
        db.table("repos")
        .select("*")
        .eq("github_url", github_url)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


async def _get_repo_by_id(db: AsyncClient, repo_id: str) -> dict | None:
    resp = await (
        db.table("repos")
        .select("*")
        .eq("id", repo_id)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


async def _update_repo(db: AsyncClient, repo_id: str, **fields) -> None:
    await (
        db.table("repos")
        .update(fields)
        .eq("id", repo_id)
        .execute()
    )


# ── Public service functions ──────────────────────────────────────────────────


async def create_or_get_repo(
    db: AsyncClient,
    github_url: str,
) -> tuple[RepoRead, bool]:
    """
    Ensure a repo record exists for the given URL.

    Returns:
        (repo, is_new) where is_new=True means a new record was created
        and analysis should be scheduled.

    Logic:
        - completed  → return existing, is_new=False (skip re-analysis)
        - pending/analyzing → return existing, is_new=False (already running)
        - failed     → create new record, is_new=True (allow retry)
        - not found  → create new record, is_new=True
    """
    # Validate URL first — raises InvalidGitHubURLError if malformed
    parse_github_url(github_url)

    existing = await _get_repo_by_url(db, github_url)
    if existing:
        status = existing.get("status")
        if status in ("pending", "analyzing", "completed"):
            return RepoRead(**existing), False
        # status == "failed" → fall through and create a new record

    owner, name = parse_github_url(github_url)

    try:
        resp = await (
            db.table("repos")
            .insert(
                {
                    "github_url": github_url,
                    "owner": owner,
                    "name": name,
                    "status": "pending",
                }
            )
            .execute()
        )
        row = resp.data[0]
    except Exception as exc:
        raise DatabaseError() from exc

    return RepoRead(**row), True


async def get_repo(db: AsyncClient, repo_id: str) -> RepoRead | None:
    """Fetch a repo by ID. Returns None if not found."""
    row = await _get_repo_by_id(db, repo_id)
    return RepoRead(**row) if row else None


async def get_repo_concepts(
    db: AsyncClient,
    repo_id: str,
) -> list[ConceptRead]:
    """Fetch all concepts for a repository."""
    return await get_concepts_for_repo(db, repo_id)


# ── Analysis pipeline (runs in BackgroundTasks) ───────────────────────────────


async def run_analysis(
    db: AsyncClient,
    github_client: GitHubClient,
    llm_client: LLMClient,
    repo_id: str,
    owner: str,
    name: str,
) -> None:
    """
    Full repository analysis pipeline.

    Runs as a FastAPI BackgroundTask — must not raise unhandled exceptions.
    All errors are caught, logged to stderr, and persisted as status=failed.
    """
    try:
        await _do_analysis(db, github_client, llm_client, repo_id, owner, name)
    except MINEError as exc:
        await _mark_failed(db, repo_id, exc.message)
    except Exception as exc:
        # Catch-all: never surface stack traces or secrets.
        await _mark_failed(db, repo_id, "Analysis failed. Please try again.")
        print(
            f"[MINE] Unexpected error during analysis for repo {repo_id}: "
            f"{type(exc).__name__}",
            file=sys.stderr,
        )


async def _do_analysis(
    db: AsyncClient,
    github_client: GitHubClient,
    llm_client: LLMClient,
    repo_id: str,
    owner: str,
    name: str,
) -> None:
    """Inner analysis — raises on any error; caller handles status transitions."""

    # 1. Mark as analyzing
    await _update_repo(db, repo_id, status="analyzing")

    # 2. Fetch GitHub metadata
    metadata = await github_client.fetch_repo_metadata(owner, name)

    # 3. Fetch README
    readme_excerpt = await github_client.fetch_readme_excerpt(
        owner, name, max_chars=settings.max_readme_chars
    )

    # 4. Fetch language breakdown
    language_breakdown = await github_client.fetch_language_breakdown(owner, name)

    # 5. Fetch top-level file tree
    top_level_tree = await github_client.fetch_top_level_tree(
        owner, name, metadata.default_branch
    )

    # 6. Fetch key files
    key_files = await github_client.fetch_key_files(
        owner,
        name,
        top_level_tree,
        max_files=settings.max_files_to_fetch,
        max_chars_per_file=settings.max_file_chars,
    )

    # 7. Persist enriched repo metadata
    await _update_repo(
        db,
        repo_id,
        description=metadata.description,
        primary_language=metadata.primary_language,
        topics=metadata.topics,
        readme_excerpt=readme_excerpt,
    )

    # 8. Assemble LLM context
    context = RepoContext(
        owner=owner,
        name=name,
        description=metadata.description,
        primary_language=metadata.primary_language,
        language_breakdown=language_breakdown,
        topics=metadata.topics,
        readme_excerpt=readme_excerpt,
        top_level_tree=top_level_tree,
        key_files=key_files,
    )

    # 9. Extract concepts via LLM
    concepts = await llm_client.extract_concepts(
        context,
        max_concepts=settings.max_concepts,
        min_concepts=settings.min_concepts,
    )

    # 10. Persist concepts
    await bulk_insert_concepts(db, repo_id, concepts)

    # 11. Mark as completed
    await _update_repo(
        db,
        repo_id,
        status="completed",
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )


async def _mark_failed(db: AsyncClient, repo_id: str, safe_message: str) -> None:
    """Persist failure status with a safe, user-facing error message."""
    try:
        await _update_repo(
            db,
            repo_id,
            status="failed",
            error_message=safe_message,
        )
    except Exception:
        pass  # If DB is also down, nothing we can do.
