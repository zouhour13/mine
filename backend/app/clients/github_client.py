"""
GitHub API client.

Responsible for all GitHub REST API communication.
Uses httpx for async HTTP.  All errors are mapped to domain exceptions
defined in core/exceptions.py — no raw HTTP details leak upward.

GITHUB_TOKEN is optional.  Public repositories work without it.
When provided, the token raises the rate limit from 60 to 5 000 req/hr.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field

import httpx

from app.core.exceptions import (
    GitHubAPIError,
    InvalidGitHubURLError,
    PrivateRepoError,
    RateLimitError,
    RepoNotFoundError,
)

GITHUB_API_BASE = "https://api.github.com"

# Files we actively try to fetch for LLM context (priority order).
KEY_FILE_CANDIDATES = [
    "README.md",
    "readme.md",
    "README.rst",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "main.py",
    "app.py",
    "index.ts",
    "index.js",
    "manage.py",
    "setup.py",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
]

# Top-level paths we never include in the tree or file fetching.
EXCLUDED_PATHS = {
    "node_modules",
    ".git",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "out",
    "coverage",
    "venv",
    ".venv",
    "env",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "htmlcov",
    "target",          # Rust/Java
    "vendor",
    ".gradle",
    ".idea",
    ".vscode",
}

# Extensions we skip when fetching file content.
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp3", ".mp4", ".wav", ".ogg",
    ".zip", ".tar", ".gz", ".bz2", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".exe", ".dll", ".so", ".dylib", ".whl",
    ".lock",   # package-lock.json, poetry.lock, etc. — large and noisy
    ".sum",    # go.sum
    ".bin",
    ".db",
    ".sqlite",
    ".parquet",
    ".csv",    # potentially large datasets
    ".jsonl",  # potentially large datasets
}


@dataclass
class RepoMetadata:
    owner: str
    name: str
    description: str | None
    primary_language: str | None
    topics: list[str]
    is_private: bool
    default_branch: str = "main"


@dataclass
class GitHubRepoContext:
    metadata: RepoMetadata
    readme_excerpt: str | None
    language_breakdown: dict[str, int]
    top_level_tree: list[str]
    key_files: dict[str, str]  # filename → truncated content


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Parse a GitHub repository URL and return (owner, repo_name).

    Accepts:
        https://github.com/owner/repo
        https://github.com/owner/repo.git
        https://github.com/owner/repo/   (trailing slash)

    Raises:
        InvalidGitHubURLError for any non-conforming input.
    """
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    pattern = r"^https?://github\.com/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)$"
    match = re.match(pattern, url)
    if not match:
        raise InvalidGitHubURLError(
            "Invalid GitHub repository URL. "
            "Expected format: https://github.com/owner/repo"
        )
    return match.group(1), match.group(2)


class GitHubClient:
    """Async client for the GitHub REST API."""

    def __init__(self, token: str | None = None) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._http = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers=headers,
            timeout=15.0,
        )

    async def _get(self, path: str) -> httpx.Response:
        """Make a GET request and map GitHub error codes to domain exceptions."""
        try:
            response = await self._http.get(path)
        except httpx.RequestError as exc:
            raise GitHubAPIError() from exc

        if response.status_code == 404:
            raise RepoNotFoundError()
        if response.status_code in (401, 403):
            raise PrivateRepoError()
        if response.status_code == 429:
            raise RateLimitError()
        if response.status_code >= 500:
            raise GitHubAPIError()

        response.raise_for_status()
        return response

    async def fetch_repo_metadata(self, owner: str, name: str) -> RepoMetadata:
        """Fetch repository metadata from GitHub."""
        resp = await self._get(f"/repos/{owner}/{name}")
        data = resp.json()

        # 403 can also be returned for private repos without raising above
        if data.get("private", False):
            raise PrivateRepoError()

        return RepoMetadata(
            owner=data["owner"]["login"],
            name=data["name"],
            description=data.get("description"),
            primary_language=data.get("language"),
            topics=data.get("topics", []),
            is_private=data.get("private", False),
            default_branch=data.get("default_branch", "main"),
        )

    async def fetch_readme_excerpt(
        self, owner: str, name: str, max_chars: int = 2_000
    ) -> str | None:
        """
        Fetch and decode the repository README.

        Returns the first `max_chars` characters of the decoded content.
        Returns None if no README exists (non-fatal).
        """
        try:
            resp = await self._get(f"/repos/{owner}/{name}/readme")
        except RepoNotFoundError:
            # README is optional — not having one is not an error.
            return None

        data = resp.json()
        encoded = data.get("content", "")
        decoded = base64.b64decode(encoded).decode("utf-8", errors="replace")
        return decoded[:max_chars] if decoded else None

    async def fetch_language_breakdown(
        self, owner: str, name: str
    ) -> dict[str, int]:
        """Fetch the byte count per language for the repository."""
        try:
            resp = await self._get(f"/repos/{owner}/{name}/languages")
            return resp.json()
        except (RepoNotFoundError, GitHubAPIError):
            return {}

    async def fetch_top_level_tree(
        self, owner: str, name: str, default_branch: str = "main"
    ) -> list[str]:
        """
        Fetch only the top-level (depth=1) file/folder names.

        Excludes known noise directories (node_modules, .git, etc.).
        """
        try:
            resp = await self._get(
                f"/repos/{owner}/{name}/git/trees/{default_branch}"
            )
        except (RepoNotFoundError, GitHubAPIError):
            return []

        tree = resp.json().get("tree", [])
        return [
            item["path"]
            for item in tree
            if item["path"] not in EXCLUDED_PATHS
        ]

    async def fetch_key_files(
        self,
        owner: str,
        name: str,
        top_level_tree: list[str],
        max_files: int = 5,
        max_chars_per_file: int = 800,
    ) -> dict[str, str]:
        """
        Fetch content of high-value files for LLM context.

        Only fetches files that:
        - Exist in the top-level tree
        - Are in the KEY_FILE_CANDIDATES priority list
        - Do not have binary/lock file extensions
        - Are within the max_files limit

        Returns a dict of {filename: truncated_content}.
        """
        tree_set = set(top_level_tree)
        fetched: dict[str, str] = {}

        for candidate in KEY_FILE_CANDIDATES:
            if len(fetched) >= max_files:
                break
            if candidate not in tree_set:
                continue

            # Skip binary / lock files
            ext = "." + candidate.rsplit(".", 1)[-1] if "." in candidate else ""
            if ext.lower() in BINARY_EXTENSIONS:
                continue

            try:
                resp = await self._http.get(
                    f"/repos/{owner}/{name}/contents/{candidate}"
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                if data.get("encoding") == "base64":
                    raw = base64.b64decode(data["content"]).decode(
                        "utf-8", errors="replace"
                    )
                    fetched[candidate] = raw[:max_chars_per_file]
            except Exception:  # noqa: BLE001
                # Non-fatal — skip this file
                continue

        return fetched

    async def aclose(self) -> None:
        await self._http.aclose()
