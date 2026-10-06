"""Schemas for concept API responses and LLM output validation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


ConceptCategory = Literal["language", "framework", "library", "architecture", "pattern", "tool"]
ConceptDifficulty = Literal["beginner", "intermediate", "advanced"]


class LLMConceptItem(BaseModel):
    """
    Pydantic model for a single concept as returned by the LLM.

    The LLM must return valid JSON matching this schema.
    If validation fails, the analysis is marked as failed.
    """

    name: str
    category: ConceptCategory
    description: str
    difficulty: ConceptDifficulty
    interview_question: str

    @field_validator("name", "description", "interview_question")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be empty.")
        return v.strip()

    @field_validator("interview_question")
    @classmethod
    def question_must_end_with_questionmark(cls, v: str) -> str:
        if not v.endswith("?"):
            v = v + "?"
        return v


class LLMConceptExtractionResult(BaseModel):
    """Wrapper around the full LLM response — expects a 'concepts' key."""

    concepts: list[LLMConceptItem]


class ConceptRead(BaseModel):
    """Response schema for a single concept."""

    id: str
    repo_id: str
    name: str
    category: ConceptCategory
    description: str
    difficulty: ConceptDifficulty
    interview_question: str
    created_at: datetime


class ConceptList(BaseModel):
    """Response schema for GET /repos/{id}/concepts."""

    repo_id: str
    total: int
    concepts: list[ConceptRead]
