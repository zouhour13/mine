"""
Gemini LLM client — concrete implementation of LLMClient Protocol.

Uses the Gemini REST API directly via httpx (no grpc / google-generativeai SDK).
This avoids native DLL dependencies that may be blocked by system policies.

API reference: https://ai.google.dev/api/generate-content
"""

from __future__ import annotations

import json
import re

import httpx
from pydantic import ValidationError

from app.core.exceptions import LLMAPIError, LLMOutputError
from app.schemas.concept import LLMConceptExtractionResult, LLMConceptItem
from app.schemas.repo import RepoContext

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-1.5-flash"

_SYSTEM_PROMPT = """\
You are an expert engineering interview coach specialising in software and AI engineering.

Your task is to analyse a GitHub repository and identify the most important technical concepts
that an engineer would need to explain clearly in a job interview.

RULES:
- Identify between {min_concepts} and {max_concepts} high-value concepts.
- Focus on concepts that require genuine understanding, not memorised definitions.
- Every interview question MUST be contextual to THIS specific repository.
- Bad question: "What is FastAPI?"
- Good question: "Why did you choose FastAPI for the backend of this project, and how does it handle request routing?"
- Prioritise concepts that reveal depth of understanding: architecture decisions, trade-offs, design patterns.
- Do NOT list every technology mentioned. Select the most interview-relevant ones.
- Categories must be one of: language, framework, library, architecture, pattern, tool
- Difficulty must be one of: beginner, intermediate, advanced

Return ONLY valid JSON — no markdown, no code fences, no explanation — in this exact format:
{{
  "concepts": [
    {{
      "name": "concept name",
      "category": "framework",
      "description": "1-2 sentence technical description of the concept and its role in this project.",
      "difficulty": "intermediate",
      "interview_question": "A contextual question about this concept in relation to this specific project?"
    }}
  ]
}}
"""

_USER_PROMPT_TEMPLATE = """\
Analyse this GitHub repository and extract the most interview-relevant technical concepts.

REPOSITORY: {owner}/{name}
DESCRIPTION: {description}
PRIMARY LANGUAGE: {primary_language}
TOPICS: {topics}

LANGUAGE BREAKDOWN:
{language_breakdown}

TOP-LEVEL FILE/FOLDER STRUCTURE:
{top_level_tree}

README EXCERPT:
{readme_excerpt}

KEY FILES:
{key_files}

Extract {min_concepts}–{max_concepts} high-value technical concepts as JSON.
"""


def _format_language_breakdown(breakdown: dict[str, int]) -> str:
    if not breakdown:
        return "Not available"
    total = sum(breakdown.values()) or 1
    lines = [
        f"  {lang}: {bytes_:,} bytes ({bytes_ / total * 100:.1f}%)"
        for lang, bytes_ in sorted(breakdown.items(), key=lambda x: -x[1])
    ]
    return "\n".join(lines)


def _format_key_files(key_files: dict[str, str]) -> str:
    if not key_files:
        return "No key files available."
    parts = []
    for filename, content in key_files.items():
        parts.append(f"--- {filename} ---\n{content}")
    return "\n\n".join(parts)


def _extract_json(text: str) -> str:
    """Strip markdown code fences if the model adds them despite instructions."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    # Try to find bare JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()


class GeminiLLMClient:
    """Gemini implementation of the LLMClient Protocol using the REST API."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._api_key = api_key
        self._model = model
        self._http = httpx.AsyncClient(
            base_url=GEMINI_API_BASE,
            timeout=60.0,
        )

    def _build_request_body(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:
        return {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json",
            },
        }

    async def extract_concepts(
        self,
        context: RepoContext,
        max_concepts: int = 20,
        min_concepts: int = 5,
    ) -> list[LLMConceptItem]:
        system_prompt = _SYSTEM_PROMPT.format(
            min_concepts=min_concepts,
            max_concepts=max_concepts,
        )
        user_prompt = _USER_PROMPT_TEMPLATE.format(
            owner=context.owner,
            name=context.name,
            description=context.description or "No description provided.",
            primary_language=context.primary_language or "Not specified",
            topics=", ".join(context.topics) if context.topics else "None",
            language_breakdown=_format_language_breakdown(context.language_breakdown),
            top_level_tree="\n".join(f"  {p}" for p in context.top_level_tree) or "  (empty)",
            readme_excerpt=context.readme_excerpt or "No README available.",
            key_files=_format_key_files(context.key_files),
            min_concepts=min_concepts,
            max_concepts=max_concepts,
        )

        url = f"/models/{self._model}:generateContent"
        body = self._build_request_body(system_prompt, user_prompt)

        try:
            resp = await self._http.post(
                url,
                json=body,
                params={"key": self._api_key},
            )
        except httpx.RequestError as exc:
            raise LLMAPIError() from exc

        if resp.status_code != 200:
            raise LLMAPIError(
                f"Gemini API returned status {resp.status_code}."
            )

        try:
            data = resp.json()
            raw_text = (
                data["candidates"][0]["content"]["parts"][0]["text"]
            )
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMOutputError(
                "Could not extract concepts: unexpected Gemini response structure."
            ) from exc

        json_text = _extract_json(raw_text)

        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise LLMOutputError(
                "Could not extract concepts: LLM returned invalid JSON."
            ) from exc

        try:
            result = LLMConceptExtractionResult.model_validate(parsed)
        except ValidationError as exc:
            raise LLMOutputError(
                "Could not extract concepts: LLM output failed schema validation."
            ) from exc

        concepts = result.concepts
        if len(concepts) < min_concepts:
            raise LLMOutputError(
                f"Could not extract concepts: only {len(concepts)} returned "
                f"(minimum {min_concepts} required)."
            )

        return concepts[:max_concepts]

    async def aclose(self) -> None:
        await self._http.aclose()
