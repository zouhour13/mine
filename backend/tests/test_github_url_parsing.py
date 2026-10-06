"""Tests for GitHub URL parsing."""

import pytest

from app.clients.github_client import parse_github_url
from app.core.exceptions import InvalidGitHubURLError


class TestParseGitHubURL:
    def test_standard_url(self):
        owner, name = parse_github_url("https://github.com/openai/gpt-4")
        assert owner == "openai"
        assert name == "gpt-4"

    def test_trailing_slash_is_stripped(self):
        owner, name = parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert name == "repo"

    def test_git_suffix_is_stripped(self):
        owner, name = parse_github_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert name == "repo"

    def test_http_scheme_accepted(self):
        owner, name = parse_github_url("http://github.com/owner/repo")
        assert owner == "owner"
        assert name == "repo"

    def test_underscores_and_dots_in_name(self):
        owner, name = parse_github_url("https://github.com/some.org/my_repo.py")
        assert owner == "some.org"
        assert name == "my_repo.py"

    def test_non_github_domain_raises(self):
        with pytest.raises(InvalidGitHubURLError):
            parse_github_url("https://gitlab.com/owner/repo")

    def test_subpath_raises(self):
        with pytest.raises(InvalidGitHubURLError):
            parse_github_url("https://github.com/owner/repo/tree/main")

    def test_missing_repo_name_raises(self):
        with pytest.raises(InvalidGitHubURLError):
            parse_github_url("https://github.com/owner")

    def test_no_scheme_raises(self):
        with pytest.raises(InvalidGitHubURLError):
            parse_github_url("github.com/owner/repo")

    def test_empty_string_raises(self):
        with pytest.raises(InvalidGitHubURLError):
            parse_github_url("")

    def test_whitespace_stripped(self):
        owner, name = parse_github_url("  https://github.com/owner/repo  ")
        assert owner == "owner"
        assert name == "repo"
