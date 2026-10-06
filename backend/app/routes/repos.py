"""
Repos routes — thin layer.

All business logic is in services/repo_service.py.
Routes only validate input, call services, and shape responses.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.database import get_db
from app.core.dependencies import GitHubClientDep, LLMClientDep
from app.core.exceptions import InvalidGitHubURLError
from app.schemas.repo import RepoCreate, RepoRead
from app.services import repo_service

router = APIRouter(prefix="/repos", tags=["repos"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RepoRead,
    summary="Submit a GitHub repository for analysis",
)
async def submit_repo(
    body: RepoCreate,
    background_tasks: BackgroundTasks,
    github_client: GitHubClientDep,
    llm_client: LLMClientDep,
    db=Depends(get_db),
) -> RepoRead:
    """
    Validate the GitHub URL, create a repo record (status=pending),
    and enqueue the analysis as a background task.

    Returns 202 immediately.  Poll GET /repos/{id} for status updates.

    If the URL has already been successfully analysed, returns the existing
    record (status=completed) without re-running analysis.
    """
    try:
        repo, is_new = await repo_service.create_or_get_repo(db, body.github_url)
    except InvalidGitHubURLError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        )

    if is_new:
        background_tasks.add_task(
            repo_service.run_analysis,
            db,
            github_client,
            llm_client,
            repo.id,
            repo.owner,
            repo.name,
        )

    return repo


@router.get(
    "/{repo_id}",
    response_model=RepoRead,
    summary="Get repository analysis status and metadata",
)
async def get_repo(
    repo_id: str,
    db=Depends(get_db),
) -> RepoRead:
    """
    Return the current status and metadata for a repository.

    Poll this endpoint every 2 seconds until status is 'completed' or 'failed'.
    """
    repo = await repo_service.get_repo(db, repo_id)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )
    return repo
