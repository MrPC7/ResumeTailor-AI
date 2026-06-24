"""Unit tests for ResumeAnalyzerAgent."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

# Import agent class directly (bypasses __init__.py singleton wiring
# which depends on the full runtime dependency chain).
from services.agents.resume_analyzer.agent import (
    ResumeAnalyzerAgent,
    ResumeAnalyzerAgentError,
)
from schemas.agent_models import CandidateProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RESUME_TEXT = """\
John Doe
john.doe@email.com | +1-555-1234

Senior Backend Engineer with 5 years of experience in Python and cloud services.

EXPERIENCE
Acme Corp — Senior Engineer (Jan 2021 - Present)
- Built microservices using FastAPI and Docker
- Led migration to AWS ECS, reducing costs by 30%

StartupXYZ — Software Engineer (2019 - 2020)
- Developed REST APIs with Flask
- Implemented CI/CD pipelines with GitHub Actions

EDUCATION
IIT Delhi — B.Tech Computer Science (2015 - 2019)

SKILLS
Python, FastAPI, Flask, Docker, AWS, PostgreSQL, Redis, Git

PROJECTS
ResumeTailor — AI-powered resume builder using FastAPI and React
Role: Full-stack developer

CERTIFICATIONS
AWS Solutions Architect Associate — Amazon (2022)
"""

VALID_LLM_RESPONSE: dict[str, Any] = {
    "skills": [
        {"name": "Python", "category": "Programming Language"},
        {"name": "FastAPI", "category": "Framework"},
        {"name": "Flask", "category": "Framework"},
        {"name": "Docker", "category": "DevOps"},
        {"name": "AWS", "category": "Cloud"},
        {"name": "PostgreSQL", "category": "Database"},
        {"name": "Redis", "category": "Database"},
        {"name": "Git", "category": "Tool"},
    ],
    "work_experience": [
        {
            "company": "Acme Corp",
            "position": "Senior Engineer",
            "duration": "Jan 2021 - Present",
            "responsibilities": [
                "Built microservices using FastAPI and Docker",
                "Led migration to AWS ECS, reducing costs by 30%",
            ],
            "technologies": ["FastAPI", "Docker", "AWS ECS"],
        },
        {
            "company": "StartupXYZ",
            "position": "Software Engineer",
            "duration": "2019 - 2020",
            "responsibilities": [
                "Developed REST APIs with Flask",
                "Implemented CI/CD pipelines with GitHub Actions",
            ],
            "technologies": ["Flask", "GitHub Actions"],
        },
    ],
    "education": [
        {
            "institution": "IIT Delhi",
            "degree": "B.Tech",
            "field_of_study": "Computer Science",
            "year": "2015 - 2019",
        }
    ],
    "projects": [
        {
            "name": "ResumeTailor",
            "description": "AI-powered resume builder using FastAPI and React",
            "technologies": ["FastAPI", "React"],
            "role": "Full-stack developer",
        }
    ],
    "certifications": [
        {"name": "AWS Solutions Architect Associate", "issuer": "Amazon", "year": "2022"}
    ],
    "total_years_experience": 5.0,
    "primary_domain": "Backend Development",
}


def _make_agent(mock_client: AsyncMock, max_retries: int = 2) -> ResumeAnalyzerAgent:
    return ResumeAnalyzerAgent(client=mock_client, max_retries=max_retries)


# ---------------------------------------------------------------------------
# Tests — extract()
# ---------------------------------------------------------------------------


class TestResumeAnalyzerAgentExtract:
    @pytest.mark.asyncio
    async def test_successful_extraction(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        profile = await agent.extract(SAMPLE_RESUME_TEXT)

        assert isinstance(profile, CandidateProfile)
        assert len(profile.skills) == 8
        assert profile.skills[0].name == "Python"
        assert len(profile.work_experience) == 2
        assert profile.work_experience[0].company == "Acme Corp"
        assert len(profile.education) == 1
        assert len(profile.projects) == 1
        assert len(profile.certifications) == 1
        assert profile.total_years_experience == 5.0
        assert profile.primary_domain == "Backend Development"
        mock_client.generate_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_unwraps_single_key_response(self) -> None:
        """LLM sometimes wraps the response in a top-level key."""
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = {"candidate_profile": VALID_LLM_RESPONSE}

        agent = _make_agent(mock_client)
        profile = await agent.extract(SAMPLE_RESUME_TEXT)

        assert isinstance(profile, CandidateProfile)
        assert len(profile.skills) == 8

    @pytest.mark.asyncio
    async def test_retries_on_parse_error(self) -> None:
        """Agent should retry on LLMParseError then succeed."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            LLMParseError("bad json"),
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        profile = await agent.extract(SAMPLE_RESUME_TEXT)

        assert isinstance(profile, CandidateProfile)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_validation_error(self) -> None:
        """Agent should retry when Pydantic validation fails."""
        mock_client = AsyncMock()
        # First call returns invalid structure, second succeeds
        mock_client.generate_json.side_effect = [
            {"skills": "not_a_list"},  # will fail validation
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        profile = await agent.extract(SAMPLE_RESUME_TEXT)

        assert isinstance(profile, CandidateProfile)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        """Agent raises ResumeAnalyzerAgentError after exhausting retries."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("always bad")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(ResumeAnalyzerAgentError, match="after 3 attempt"):
            await agent.extract(SAMPLE_RESUME_TEXT)

        assert mock_client.generate_json.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_immediately_on_api_error(self) -> None:
        """LLMAPIError is non-retryable — should raise immediately."""
        from services.llm import LLMAPIError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMAPIError("quota exceeded")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(LLMAPIError):
            await agent.extract(SAMPLE_RESUME_TEXT)

        assert mock_client.generate_json.call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_clamped_to_minimum_1(self) -> None:
        """max_retries=0 should be clamped to 1."""
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client, max_retries=0)
        assert agent._max_retries == 1

        profile = await agent.extract(SAMPLE_RESUME_TEXT)
        assert isinstance(profile, CandidateProfile)


# ---------------------------------------------------------------------------
# Tests — run() (pipeline interface)
# ---------------------------------------------------------------------------


class TestResumeAnalyzerAgentRun:
    @pytest.mark.asyncio
    async def test_run_returns_candidate_profile_in_context(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.run({"raw_resume_text": SAMPLE_RESUME_TEXT})

        assert "candidate_profile" in result
        assert isinstance(result["candidate_profile"], CandidateProfile)

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_raw_text(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({})

    @pytest.mark.asyncio
    async def test_run_propagates_agent_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("bad")

        agent = _make_agent(mock_client, max_retries=1)
        with pytest.raises(ResumeAnalyzerAgentError):
            await agent.run({"raw_resume_text": SAMPLE_RESUME_TEXT})
