"""
Concept service — persistence and deduplication.

supabase-py AsyncClient: .table() is synchronous (returns a builder),
only .execute() is async. Pattern: await db.table(...).select(...).execute()
"""

from __future__ import annotations

from supabase import AsyncClient

from app.core.exceptions import DatabaseError
from app.schemas.concept import ConceptRead, LLMConceptItem


async def bulk_insert_concepts(
    db: AsyncClient,
    repo_id: str,
    concepts: list[LLMConceptItem],
) -> None:
    """
    Insert concepts into the database.

    Uses upsert with ignore_duplicates=True to honour
    UNIQUE(repo_id, name) without raising on duplicates.
    """
    if not concepts:
        return

    rows = [
        {
            "repo_id": repo_id,
            "name": concept.name,
            "category": concept.category,
            "description": concept.description,
            "difficulty": concept.difficulty,
            "interview_question": concept.interview_question,
        }
        for concept in concepts
    ]

    try:
        await (
            db.table("concepts")
            .upsert(rows, on_conflict="repo_id,name", ignore_duplicates=True)
            .execute()
        )
    except Exception as exc:
        raise DatabaseError() from exc


async def get_concepts_for_repo(
    db: AsyncClient,
    repo_id: str,
) -> list[ConceptRead]:
    """Fetch all concepts for a repository, ordered by creation time."""
    try:
        resp = await (
            db.table("concepts")
            .select("*")
            .eq("repo_id", repo_id)
            .order("created_at")
            .execute()
        )
        return [ConceptRead(**row) for row in resp.data]
    except Exception as exc:
        raise DatabaseError() from exc
