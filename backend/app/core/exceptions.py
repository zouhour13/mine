"""
Domain exceptions for MINE backend.

Each exception maps to a safe, user-facing error message.
Raw exception details, API keys, and stack traces must never
be surfaced to the frontend.
"""

from __future__ import annotations


class MINEError(Exception):
    """Base class for all MINE domain errors."""

    default_message: str = "An unexpected error occurred. Please try again."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


# ── GitHub errors ─────────────────────────────────────────────────────────────


class InvalidGitHubURLError(MINEError):
    default_message = "Invalid GitHub repository URL."


class RepoNotFoundError(MINEError):
    default_message = "Repository not found on GitHub."


class PrivateRepoError(MINEError):
    default_message = "This repository is private or inaccessible."


class RateLimitError(MINEError):
    default_message = "GitHub API rate limit reached. Please try again shortly."


class GitHubAPIError(MINEError):
    default_message = "GitHub API is temporarily unavailable."


# ── LLM errors ────────────────────────────────────────────────────────────────


class LLMOutputError(MINEError):
    default_message = "Could not extract concepts from this repository. Please try again."


class LLMAPIError(MINEError):
    default_message = "The AI service is temporarily unavailable."


# ── Database errors ───────────────────────────────────────────────────────────


class DatabaseError(MINEError):
    default_message = "A database error occurred. Please try again."
