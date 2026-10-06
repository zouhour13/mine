"""
Concepts routes — thin layer.

Returns extracted concepts for a completed repository analysis.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.schemas.concept import ConceptList
from app.services import repo_service

router = APIRouter(prefix="/repos", tags=["concepts"])


@router.get(
    "/{repo_id}/concepts",
    response_model=ConceptList,
    summary="Get extracted concepts for a repository",
)
async def get_concepts(
    repo_id: str,
    db=Depends(get_db),
) -> ConceptList:
    """
    Return the extracted technical concepts for a completed repository analysis.

    Raises 409 if the analysis is not yet complete.
    Raises 404 if the repository does not exist.
    """
    repo = await repo_service.get_repo(db, repo_id)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    if repo.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository analysis is not yet complete.",
        )

    concepts = await repo_service.get_repo_concepts(db, repo_id)

    return ConceptList(
        repo_id=repo_id,
        total=len(concepts),
        concepts=concepts,
    )
