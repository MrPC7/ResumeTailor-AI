"""Unit tests for JDAnalyzerAgent."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import JobProfile
from services.agents.jd_analyzer.agent import (
    JDAnalyzerAgent,
    JDAnalyzerAgentError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_JD_TEXT = """\
Senior Backend Engineer — Acme Corp

We are looking for a Senior Backend Engineer to join our platform team.

Requirements:
- 5+ years of experience in backend development
- Strong proficiency in Python and FastAPI
- Experience with PostgreSQL and Redis
- Familiarity with Docker and Kubernetes
- Understanding of microservices architecture

Nice to have:
- Experience with AWS (ECS, Lambda, S3)
- Knowledge of GraphQL
- Contributions to open-source projects

Responsibilities:
- Design and implement scalable REST APIs
- Lead architecture discussions and code reviews
- Mentor junior engineers
- Collaborate with product and frontend teams
- Optimize database queries and system performance
"""

VALID_LLM_RESPONSE: dict[str, Any] = {
    "role": "Senior Backend Engineer",
    "seniority": "Senior",
    "must_have_skills": [
        {"name": "Python", "category": "Programming Language"},
        {"name": "FastAPI", "category": "Framework"},
        {"name": "PostgreSQL", "category": "Database"},
        {"name": "Redis", "category": "Database"},
        {"name": "Docker", "category": "DevOps"},
        {"name": "Kubernetes", "category": "DevOps"},
        {"name": "Microservices", "category": "Domain"},
    ],
    "preferred_skills": [
        {"name": "AWS", "category": "Cloud"},
        {"name": "GraphQL", "category": "Framework"},
        {"name": "Open Source", "category": "Other"},
    ],
    "responsibilities": [
        {"description": "Design and implement scalable REST APIs", "priority": "high"},
        {"description": "Lead architecture discussions and code reviews", "priority": "high"},
        {"description": "Mentor junior engineers", "priority": "medium"},
        {"description": "Collaborate with product and frontend teams", "priority": "medium"},
        {"description": "Optimize database queries and system performance", "priority": "medium"},
    ],
    "experience_required": {
        "min_years": 5.0,
        "max_years": None,
        "domain": "Backend Development",
    },
}


def _make_agent(mock_client: AsyncMock, max_retries: int = 2) -> JDAnalyzerAgent:
    return JDAnalyzerAgent(client=mock_client, max_retries=max_retries)


# ---------------------------------------------------------------------------
# Tests — extract()
# ---------------------------------------------------------------------------


class TestJDAnalyzerAgentExtract:
    @pytest.mark.asyncio
    async def test_successful_extraction(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        profile = await agent.extract(SAMPLE_JD_TEXT)

        assert isinstance(profile, JobProfile)
        assert profile.role == "Senior Backend Engineer"
        assert profile.seniority == "Senior"
        assert len(profile.must_have_skills) == 7
        assert profile.must_have_skills[0].name == "Python"
        assert len(profile.preferred_skills) == 3
        assert len(profile.responsibilities) == 5
        assert profile.responsibilities[0].priority == "high"
        assert profile.experience_required.min_years == 5.0
        assert profile.experience_required.max_years is None
        assert profile.experience_required.domain == "Backend Development"
        mock_client.generate_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_unwraps_single_key_response(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = {"job_profile": VALID_LLM_RESPONSE}

        agent = _make_agent(mock_client)
        profile = await agent.extract(SAMPLE_JD_TEXT)

        assert isinstance(profile, JobProfile)
        assert profile.role == "Senior Backend Engineer"

    @pytest.mark.asyncio
    async def test_retries_on_parse_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            LLMParseError("bad json"),
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        profile = await agent.extract(SAMPLE_JD_TEXT)

        assert isinstance(profile, JobProfile)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_validation_error(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            {"must_have_skills": "not_a_list"},  # will fail validation
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        profile = await agent.extract(SAMPLE_JD_TEXT)

        assert isinstance(profile, JobProfile)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("always bad")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(JDAnalyzerAgentError, match="after 3 attempt"):
            await agent.extract(SAMPLE_JD_TEXT)

        assert mock_client.generate_json.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_immediately_on_api_error(self) -> None:
        from services.llm import LLMAPIError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMAPIError("quota exceeded")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(LLMAPIError):
            await agent.extract(SAMPLE_JD_TEXT)

        assert mock_client.generate_json.call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_clamped_to_minimum_1(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client, max_retries=0)
        assert agent._max_retries == 1

        profile = await agent.extract(SAMPLE_JD_TEXT)
        assert isinstance(profile, JobProfile)


# ---------------------------------------------------------------------------
# Tests — run() (pipeline interface)
# ---------------------------------------------------------------------------


class TestJDAnalyzerAgentRun:
    @pytest.mark.asyncio
    async def test_run_returns_job_profile_in_context(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.run({"raw_jd_text": SAMPLE_JD_TEXT})

        assert "job_profile" in result
        assert isinstance(result["job_profile"], JobProfile)

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_raw_jd(self) -> None:
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
        with pytest.raises(JDAnalyzerAgentError):
            await agent.run({"raw_jd_text": SAMPLE_JD_TEXT})
