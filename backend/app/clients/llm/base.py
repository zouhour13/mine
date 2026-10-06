"""
LLM client protocol.

Defines the interface that all LLM provider implementations must satisfy.
Uses structural typing (Protocol) — no inheritance required.

To add a new provider:
1. Create clients/llm/<provider>_client.py
2. Implement the extract_concepts method matching the Protocol signature
3. Add a branch in core/dependencies.py _build_llm_client()
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.concept import LLMConceptItem
from app.schemas.repo import RepoContext


@runtime_checkable
class LLMClient(Protocol):
    async def extract_concepts(
        self,
        context: RepoContext,
        max_concepts: int,
        min_concepts: int,
    ) -> list[LLMConceptItem]:
        """
        Extract interview-relevant technical concepts from a repository context.

        Args:
            context:      Assembled repository metadata and file excerpts.
            max_concepts: Upper bound on the number of concepts to return.
            min_concepts: Lower bound — raise LLMOutputError if fewer returned.

        Returns:
            A validated list of LLMConceptItem instances.

        Raises:
            LLMOutputError: If the LLM returns invalid JSON or fails validation.
            LLMAPIError:    If the LLM provider returns an error.
        """
        ...
