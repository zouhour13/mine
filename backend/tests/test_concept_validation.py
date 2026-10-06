"""Tests for LLM concept output validation (Pydantic schemas)."""

import json

import pytest
from pydantic import ValidationError

from app.schemas.concept import LLMConceptExtractionResult, LLMConceptItem


def _make_valid_concept(**overrides) -> dict:
    base = {
        "name": "FastAPI dependency injection",
        "category": "framework",
        "description": "FastAPI resolves typed dependencies at request time.",
        "difficulty": "intermediate",
        "interview_question": "Why did you use dependency injection in this project?",
    }
    base.update(overrides)
    return base


class TestLLMConceptItem:
    def test_valid_concept(self):
        item = LLMConceptItem(**_make_valid_concept())
        assert item.name == "FastAPI dependency injection"
        assert item.category == "framework"
        assert item.difficulty == "intermediate"

    def test_question_gets_questionmark_appended(self):
        item = LLMConceptItem(**_make_valid_concept(interview_question="Why did you use it"))
        assert item.interview_question.endswith("?")

    def test_invalid_category_raises(self):
        with pytest.raises(ValidationError):
            LLMConceptItem(**_make_valid_concept(category="database"))

    def test_invalid_difficulty_raises(self):
        with pytest.raises(ValidationError):
            LLMConceptItem(**_make_valid_concept(difficulty="expert"))

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            LLMConceptItem(**_make_valid_concept(name=""))

    def test_empty_description_raises(self):
        with pytest.raises(ValidationError):
            LLMConceptItem(**_make_valid_concept(description="   "))

    def test_empty_question_raises(self):
        with pytest.raises(ValidationError):
            LLMConceptItem(**_make_valid_concept(interview_question=""))

    def test_whitespace_stripped_from_fields(self):
        item = LLMConceptItem(**_make_valid_concept(name="  FastAPI  "))
        assert item.name == "FastAPI"


class TestLLMConceptExtractionResult:
    def test_valid_list(self):
        data = {"concepts": [_make_valid_concept(), _make_valid_concept(name="Docker")]}
        result = LLMConceptExtractionResult.model_validate(data)
        assert len(result.concepts) == 2

    def test_empty_list_is_valid_at_schema_level(self):
        # The min_concepts check is enforced in the LLM client, not the schema.
        result = LLMConceptExtractionResult.model_validate({"concepts": []})
        assert result.concepts == []

    def test_missing_concepts_key_raises(self):
        with pytest.raises(ValidationError):
            LLMConceptExtractionResult.model_validate({"items": []})

    def test_invalid_concept_inside_list_raises(self):
        bad_concept = _make_valid_concept(category="INVALID")
        with pytest.raises(ValidationError):
            LLMConceptExtractionResult.model_validate({"concepts": [bad_concept]})

    def test_parse_from_json_string(self):
        payload = json.dumps({"concepts": [_make_valid_concept()]})
        result = LLMConceptExtractionResult.model_validate_json(payload)
        assert len(result.concepts) == 1
