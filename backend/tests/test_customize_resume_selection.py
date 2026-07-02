from __future__ import annotations

from typing import Any

import pytest

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.customize_resume import CustomizeResumeRequest
from schemas.extract_resume import ExtractResumeResponse
from services.resume_customizer.customizer import ResumeCustomizer


def sample_resume() -> ExtractResumeResponse:
    return ExtractResumeResponse(
        name="Ada Lovelace",
        email="ada@example.com",
        phone="555-0100",
        summary="Backend engineer.",
        skills=["Python", "FastAPI", "SQL"],
        experience=[],
        education=[],
        projects=[],
    )


def sample_jd() -> AnalyzeJDResponse:
    return AnalyzeJDResponse(
        role="Backend Engineer",
        seniority="Senior",
        requiredSkills=["Python"],
        preferredSkills=["FastAPI"],
        atsKeywords=["APIs"],
        responsibilities=["Build APIs"],
    )


class CapturingClient:
    def __init__(self) -> None:
        self.prompt: str | None = None
        self.prompts: list[str] = []

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        self.prompt = prompt
        self.prompts.append(prompt)
        return {
            "customizedResume": {
                "summary": "Backend engineer focused on Python APIs.",
                "skills": ["Python", "FastAPI", "SQL"],
                "experience": [],
                "education": [],
                "projects": [],
            },
            "suggestions": [],
        }


def test_request_parses_selected_suggestion_ids() -> None:
    payload = CustomizeResumeRequest.model_validate(
        {
            "resume": sample_resume().model_dump(),
            "jd": sample_jd().model_dump(),
            "selectedSuggestionIds": ["s1"],
            "suggestions": [
                {
                    "id": "s1",
                    "title": "Rewrite summary",
                    "description": "Mention Python APIs.",
                }
            ],
        }
    )

    assert payload.selected_suggestion_ids == ["s1"]
    assert payload.suggestions[0].id == "s1"


@pytest.mark.asyncio
async def test_no_selected_suggestions_returns_original_without_llm_call() -> None:
    client = CapturingClient()
    customizer = ResumeCustomizer(client=client, max_retries=1)
    resume = sample_resume()

    result = await customizer.customize(
        CustomizeResumeRequest(
            resume=resume,
            jd=sample_jd(),
            selectedSuggestionIds=[],
            suggestions=[],
        )
    )

    assert result.customizedResume == resume
    assert result.suggestions == []
    assert client.prompt is None


@pytest.mark.asyncio
async def test_only_selected_suggestion_content_reaches_prompt() -> None:
    client = CapturingClient()
    customizer = ResumeCustomizer(client=client, max_retries=1)

    await customizer.customize(
        CustomizeResumeRequest(
            resume=sample_resume(),
            jd=sample_jd(),
            selectedSuggestionIds=["s1"],
            suggestions=[
                {
                    "id": "s1",
                    "title": "Rewrite summary",
                    "description": "Mention Python APIs.",
                },
                {
                    "id": "s2",
                    "title": "Unwanted certification",
                    "description": "Add a Kubernetes certification.",
                },
            ],
        )
    )

    assert client.prompts
    customization_prompt = client.prompts[0]
    assert "Mention Python APIs" in customization_prompt
    assert "s2" in customization_prompt
    assert "Add a Kubernetes certification" not in customization_prompt
