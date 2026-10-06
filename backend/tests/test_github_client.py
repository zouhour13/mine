"""Tests for GitHub API client — all HTTP calls are mocked with respx."""

import base64
import json

import pytest
import respx
from httpx import Response

from app.clients.github_client import GitHubClient
from app.core.exceptions import (
    GitHubAPIError,
    PrivateRepoError,
    RateLimitError,
    RepoNotFoundError,
)


def _make_client(token: str | None = None) -> GitHubClient:
    return GitHubClient(token=token)


@pytest.fixture
def client():
    return _make_client()


@pytest.fixture
def authed_client():
    return _make_client(token="ghp_test_token")


class TestFetchRepoMetadata:
    @respx.mock
    async def test_success(self, client):
        respx.get("https://api.github.com/repos/owner/repo").mock(
            return_value=Response(
                200,
                json={
                    "owner": {"login": "owner"},
                    "name": "repo",
                    "description": "A test repo",
                    "language": "Python",
                    "topics": ["fastapi", "ml"],
                    "private": False,
                    "default_branch": "main",
                },
            )
        )
        meta = await client.fetch_repo_metadata("owner", "repo")
        assert meta.owner == "owner"
        assert meta.name == "repo"
        assert meta.primary_language == "Python"
        assert meta.topics == ["fastapi", "ml"]
        assert meta.is_private is False

    @respx.mock
    async def test_404_raises_repo_not_found(self, client):
        respx.get("https://api.github.com/repos/owner/missing").mock(
            return_value=Response(404, json={"message": "Not Found"})
        )
        with pytest.raises(RepoNotFoundError):
            await client.fetch_repo_metadata("owner", "missing")

    @respx.mock
    async def test_403_raises_private_repo(self, client):
        respx.get("https://api.github.com/repos/owner/private-repo").mock(
            return_value=Response(403, json={"message": "Forbidden"})
        )
        with pytest.raises(PrivateRepoError):
            await client.fetch_repo_metadata("owner", "private-repo")

    @respx.mock
    async def test_429_raises_rate_limit(self, client):
        respx.get("https://api.github.com/repos/owner/repo").mock(
            return_value=Response(429, json={"message": "rate limit exceeded"})
        )
        with pytest.raises(RateLimitError):
            await client.fetch_repo_metadata("owner", "repo")

    @respx.mock
    async def test_private_flag_in_body_raises(self, client):
        respx.get("https://api.github.com/repos/owner/secret").mock(
            return_value=Response(
                200,
                json={
                    "owner": {"login": "owner"},
                    "name": "secret",
                    "description": None,
                    "language": None,
                    "topics": [],
                    "private": True,
                    "default_branch": "main",
                },
            )
        )
        with pytest.raises(PrivateRepoError):
            await client.fetch_repo_metadata("owner", "secret")

    def test_token_sets_auth_header(self, authed_client):
        headers = authed_client._http.headers
        assert "authorization" in {k.lower() for k in headers}
        auth_value = dict(authed_client._http.headers)["authorization"]
        assert auth_value == "Bearer ghp_test_token"

    def test_no_token_no_auth_header(self, client):
        header_keys = {k.lower() for k in client._http.headers}
        assert "authorization" not in header_keys


class TestFetchReadmeExcerpt:
    @respx.mock
    async def test_success(self, client):
        content = "# My Project\n\nThis is a test README."
        encoded = base64.b64encode(content.encode()).decode()
        respx.get("https://api.github.com/repos/owner/repo/readme").mock(
            return_value=Response(200, json={"content": encoded, "encoding": "base64"})
        )
        result = await client.fetch_readme_excerpt("owner", "repo", max_chars=100)
        assert result == content

    @respx.mock
    async def test_truncated_to_max_chars(self, client):
        content = "A" * 5000
        encoded = base64.b64encode(content.encode()).decode()
        respx.get("https://api.github.com/repos/owner/repo/readme").mock(
            return_value=Response(200, json={"content": encoded, "encoding": "base64"})
        )
        result = await client.fetch_readme_excerpt("owner", "repo", max_chars=100)
        assert result == "A" * 100

    @respx.mock
    async def test_404_returns_none(self, client):
        respx.get("https://api.github.com/repos/owner/no-readme/readme").mock(
            return_value=Response(404, json={"message": "Not Found"})
        )
        result = await client.fetch_readme_excerpt("owner", "no-readme")
        assert result is None
