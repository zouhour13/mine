"""
Tests for repo_service — all DB and client calls are mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import LLMOutputError, RepoNotFoundError
from app.schemas.concept import LLMConceptItem
from app.schemas.repo import RepoRead
from app.services import repo_service


def _make_repo_row(status="pending", **overrides) -> dict:
    base = {
        "id": "repo-uuid-123",
        "github_url": "https://github.com/owner/repo",
        "owner": "owner",
        "name": "repo",
        "description": None,
        "primary_language": None,
        "topics": [],
        "status": status,
        "error_message": None,
        "created_at": "2026-10-06T11:00:00+00:00",
        "analyzed_at": None,
    }
    base.update(overrides)
    return base


def _make_concept() -> LLMConceptItem:
    return LLMConceptItem(
        name="FastAPI dependency injection",
        category="framework",
        description="FastAPI resolves typed dependencies at request time.",
        difficulty="intermediate",
        interview_question="Why did you use dependency injection here?",
    )


def _make_mock_db(existing_row: dict | None = None, insert_row: dict | None = None):
    """
    Build a mock Supabase AsyncClient that matches the supabase-py builder pattern.

    Pattern: db.table(...) → sync builder → .execute() → awaitable
    db.table() is NOT async — it returns a MagicMock builder.
    Only .execute() is async (AsyncMock).
    """
    db = MagicMock()  # NOT AsyncMock — table() is synchronous

    _insert_row = insert_row or _make_repo_row()

    # Build the chainable builder mock — each method returns the same mock
    builder = MagicMock()
    execute_mock = AsyncMock()
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.limit.return_value = builder
    builder.order.return_value = builder
    builder.insert.return_value = builder
    builder.update.return_value = builder
    builder.upsert.return_value = builder
    builder.execute = execute_mock

    # Default execute returns for select
    execute_mock.return_value = MagicMock(
        data=[existing_row] if existing_row else []
    )

    db.table.return_value = builder

    # Store references for assertions
    db._builder = builder
    db._execute_mock = execute_mock
    db._insert_row = _insert_row

    return db


def _db_returning_insert(insert_row: dict):
    """Return a db mock that returns insert_row on insert."""
    db = MagicMock()
    builder = MagicMock()

    select_execute = AsyncMock(return_value=MagicMock(data=[]))
    insert_execute = AsyncMock(return_value=MagicMock(data=[insert_row]))
    update_execute = AsyncMock(return_value=MagicMock(data=[]))
    upsert_execute = AsyncMock(return_value=MagicMock(data=[]))

    # We need to distinguish between select/insert/update/upsert calls
    # Use side_effect on execute based on what was last called
    call_tracker = {"last": None}

    def track_select(*a, **kw):
        call_tracker["last"] = "select"
        return builder

    def track_insert(*a, **kw):
        call_tracker["last"] = "insert"
        return builder

    def track_update(*a, **kw):
        call_tracker["last"] = "update"
        return builder

    def track_upsert(*a, **kw):
        call_tracker["last"] = "upsert"
        return builder

    async def smart_execute():
        last = call_tracker["last"]
        if last == "insert":
            return MagicMock(data=[insert_row])
        if last in ("update", "upsert"):
            return MagicMock(data=[])
        return MagicMock(data=[])

    builder.select = MagicMock(side_effect=track_select)
    builder.insert = MagicMock(side_effect=track_insert)
    builder.update = MagicMock(side_effect=track_update)
    builder.upsert = MagicMock(side_effect=track_upsert)
    builder.eq = MagicMock(return_value=builder)
    builder.limit = MagicMock(return_value=builder)
    builder.order = MagicMock(return_value=builder)
    builder.execute = smart_execute

    db.table.return_value = builder
    db._builder = builder
    db._call_tracker = call_tracker

    return db


class TestCreateOrGetRepo:
    async def test_new_repo_is_created(self):
        db = _db_returning_insert(_make_repo_row())
        repo, is_new = await repo_service.create_or_get_repo(
            db, "https://github.com/owner/repo"
        )
        assert is_new is True
        assert repo.status == "pending"

    async def test_completed_repo_returns_existing(self):
        existing = _make_repo_row(status="completed")
        db = _make_mock_db(existing_row=existing)
        repo, is_new = await repo_service.create_or_get_repo(
            db, "https://github.com/owner/repo"
        )
        assert is_new is False
        assert repo.status == "completed"

    async def test_pending_repo_returns_existing(self):
        existing = _make_repo_row(status="pending")
        db = _make_mock_db(existing_row=existing)
        _, is_new = await repo_service.create_or_get_repo(
            db, "https://github.com/owner/repo"
        )
        assert is_new is False

    async def test_analyzing_repo_returns_existing(self):
        existing = _make_repo_row(status="analyzing")
        db = _make_mock_db(existing_row=existing)
        _, is_new = await repo_service.create_or_get_repo(
            db, "https://github.com/owner/repo"
        )
        assert is_new is False

    async def test_failed_repo_creates_new(self):
        """A failed repo allows re-analysis."""
        existing = _make_repo_row(status="failed")
        # select returns failed, insert returns new pending
        db = _db_returning_insert(_make_repo_row(status="pending"))

        # Override select to return the failed existing row
        call_tracker = db._call_tracker
        builder = db._builder
        new_row = _make_repo_row(status="pending")

        async def smart_execute_with_failed():
            last = call_tracker.get("last")
            if last == "insert":
                return MagicMock(data=[new_row])
            if last in ("update", "upsert"):
                return MagicMock(data=[])
            # select → return failed existing
            return MagicMock(data=[existing])

        builder.execute = smart_execute_with_failed

        _, is_new = await repo_service.create_or_get_repo(
            db, "https://github.com/owner/repo"
        )
        assert is_new is True


class TestRunAnalysis:
    def _make_github_client(self):
        github_client = AsyncMock()
        github_client.fetch_repo_metadata.return_value = MagicMock(
            description="A repo",
            primary_language="Python",
            topics=["fastapi"],
            default_branch="main",
        )
        github_client.fetch_readme_excerpt.return_value = "# Test"
        github_client.fetch_language_breakdown.return_value = {"Python": 10000}
        github_client.fetch_top_level_tree.return_value = ["main.py", "requirements.txt"]
        github_client.fetch_key_files.return_value = {"requirements.txt": "fastapi\n"}
        return github_client

    async def test_happy_path_sets_completed(self):
        update_calls = []

        async def smart_execute():
            last = call_tracker.get("last")
            if last == "insert":
                return MagicMock(data=[_make_repo_row()])
            if last == "update":
                update_calls.append(dict(last_update_data))
                return MagicMock(data=[])
            if last == "upsert":
                return MagicMock(data=[])
            return MagicMock(data=[])

        last_update_data = {}
        call_tracker = {}

        db = MagicMock()
        builder = MagicMock()

        def track_update(data, **kw):
            last_update_data.clear()
            last_update_data.update(data)
            call_tracker["last"] = "update"
            return builder

        builder.select = MagicMock(side_effect=lambda *a, **kw: _set_and_return(call_tracker, "select", builder))
        builder.insert = MagicMock(side_effect=lambda *a, **kw: _set_and_return(call_tracker, "insert", builder))
        builder.upsert = MagicMock(side_effect=lambda *a, **kw: _set_and_return(call_tracker, "upsert", builder))
        builder.update = MagicMock(side_effect=track_update)
        builder.eq = MagicMock(return_value=builder)
        builder.limit = MagicMock(return_value=builder)
        builder.order = MagicMock(return_value=builder)
        builder.execute = smart_execute
        db.table.return_value = builder

        llm_client = AsyncMock()
        llm_client.extract_concepts.return_value = [_make_concept()]

        await repo_service.run_analysis(
            db, self._make_github_client(), llm_client, "repo-uuid-123", "owner", "repo"
        )

        statuses = [c.get("status") for c in update_calls if "status" in c]
        assert "completed" in statuses

    async def test_github_error_sets_failed_with_safe_message(self):
        update_calls = []

        async def smart_execute():
            last = call_tracker.get("last")
            if last == "update":
                update_calls.append(dict(last_update_data))
            return MagicMock(data=[])

        last_update_data = {}
        call_tracker = {}

        db = MagicMock()
        builder = MagicMock()

        def track_update(data, **kw):
            last_update_data.clear()
            last_update_data.update(data)
            call_tracker["last"] = "update"
            return builder

        builder.select = MagicMock(return_value=builder)
        builder.update = MagicMock(side_effect=track_update)
        builder.upsert = MagicMock(return_value=builder)
        builder.insert = MagicMock(return_value=builder)
        builder.eq = MagicMock(return_value=builder)
        builder.limit = MagicMock(return_value=builder)
        builder.order = MagicMock(return_value=builder)
        builder.execute = smart_execute
        db.table.return_value = builder

        github_client = AsyncMock()
        github_client.fetch_repo_metadata.side_effect = RepoNotFoundError()
        llm_client = AsyncMock()

        await repo_service.run_analysis(
            db, github_client, llm_client, "repo-uuid-123", "owner", "repo"
        )

        statuses = [c.get("status") for c in update_calls if "status" in c]
        assert "failed" in statuses

        # Verify error message is safe
        failed_calls = [c for c in update_calls if c.get("status") == "failed"]
        assert failed_calls
        msg = failed_calls[0].get("error_message", "")
        assert "secret" not in msg.lower()
        assert "traceback" not in msg.lower()
        assert len(msg) > 0

    async def test_llm_error_sets_failed(self):
        update_calls = []

        async def smart_execute():
            last = call_tracker.get("last")
            if last == "update":
                update_calls.append(dict(last_update_data))
            return MagicMock(data=[])

        last_update_data = {}
        call_tracker = {}

        db = MagicMock()
        builder = MagicMock()

        def track_update(data, **kw):
            last_update_data.clear()
            last_update_data.update(data)
            call_tracker["last"] = "update"
            return builder

        builder.select = MagicMock(return_value=builder)
        builder.update = MagicMock(side_effect=track_update)
        builder.upsert = MagicMock(return_value=builder)
        builder.insert = MagicMock(return_value=builder)
        builder.eq = MagicMock(return_value=builder)
        builder.limit = MagicMock(return_value=builder)
        builder.order = MagicMock(return_value=builder)
        builder.execute = smart_execute
        db.table.return_value = builder

        llm_client = AsyncMock()
        llm_client.extract_concepts.side_effect = LLMOutputError()

        await repo_service.run_analysis(
            db, self._make_github_client(), llm_client, "repo-uuid-123", "owner", "repo"
        )

        statuses = [c.get("status") for c in update_calls if "status" in c]
        assert "failed" in statuses


def _set_and_return(tracker: dict, key: str, val):
    tracker["last"] = key
    return val
