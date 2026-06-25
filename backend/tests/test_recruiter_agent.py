"""Unit tests for RecruiterAgent."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    RequiredSkill,
    PreferredSkill,
    Responsibility,
    ExperienceRequirement,
    Skill,
    WorkExperience,
    Project,
)
from services.agents.recruiter.agent import (
    RecruiterAgent,
    RecruiterAgentError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


CANDIDATE_PROFILE = CandidateProfile(
    skills=[
        Skill(name="Python", category="Programming Language"),
        Skill(name="FastAPI", category="Framework"),
        Skill(name="PostgreSQL", category="Database"),
        Skill(name="Docker", category="DevOps"),
        Skill(name="AWS", category="Cloud"),
        Skill(name="Redis", category="Database"),
    ],
    work_experience=[
        WorkExperience(
            company="Acme Corp",
            position="Senior Backend Engineer",
            duration="Jan 2021 - Present",
            responsibilities=["Built microservices with FastAPI", "Led AWS migration"],
            technologies=["Python", "FastAPI", "Docker", "AWS"],
        ),
        WorkExperience(
            company="StartupXYZ",
            position="Software Engineer",
            duration="2019 - 2020",
            responsibilities=["Developed REST APIs", "Implemented CI/CD"],
            technologies=["Python", "Flask", "PostgreSQL"],
        ),
    ],
    projects=[
        Project(
            name="ResumeTailor",
            description="AI-powered resume builder",
            technologies=["FastAPI", "React", "Docker"],
            role="Full-stack developer",
        ),
    ],
    total_years_experience=5.0,
    primary_domain="Backend Development",
)

JOB_PROFILE = JobProfile(
    role="Senior Backend Engineer",
    seniority="Senior",
    must_have_skills=[
        RequiredSkill(name="Python", category="Programming Language"),
        RequiredSkill(name="FastAPI", category="Framework"),
        RequiredSkill(name="PostgreSQL", category="Database"),
        RequiredSkill(name="Docker", category="DevOps"),
        RequiredSkill(name="Kubernetes", category="DevOps"),
    ],
    preferred_skills=[
        PreferredSkill(name="AWS", category="Cloud"),
        PreferredSkill(name="GraphQL", category="Framework"),
    ],
    responsibilities=[
        Responsibility(description="Design scalable APIs", priority="high"),
        Responsibility(description="Mentor junior engineers", priority="medium"),
    ],
    experience_required=ExperienceRequirement(
        min_years=5.0,
        max_years=None,
        domain="Backend Development",
    ),
)

VALID_LLM_RESPONSE: dict[str, Any] = {
    "match_level": "good_match",
    "hiring_confidence": 72,
    "interview_probability": 78,
    "strengths": [
        "5 years backend experience meets minimum requirement",
        "Strong Python + FastAPI proficiency demonstrated in Acme Corp role",
        "Real project (ResumeTailor) shows full-stack capability with FastAPI + Docker",
        "AWS experience is a preferred skill bonus",
    ],
    "gaps": [
        "No Kubernetes experience mentioned — this is a must-have requirement",
        "No explicit mentoring/leadership evidence despite Senior role requirement",
    ],
    "verdict": "Good backend fit with one critical DevOps gap (Kubernetes); recommend phone screen.",
    "reasoning": [
        "Candidate has 5.0 years experience matching the 5-year minimum requirement",
        "4 of 5 must-have skills present (Python, FastAPI, PostgreSQL, Docker) — scores well",
        "Missing Kubernetes is significant as it's a must-have DevOps skill — reduces confidence by ~15 points",
        "Project evidence (ResumeTailor) demonstrates practical FastAPI + Docker usage — strong signal",
        "AWS experience matches preferred skill — bonus points applied",
        "Overall: solid match with one addressable gap, suitable for phone screen",
    ],
}


def _make_agent(mock_client: AsyncMock, max_retries: int = 2) -> RecruiterAgent:
    return RecruiterAgent(client=mock_client, max_retries=max_retries)


# ---------------------------------------------------------------------------
# Tests — evaluate()
# ---------------------------------------------------------------------------


class TestRecruiterAgentEvaluate:
    @pytest.mark.asyncio
    async def test_successful_evaluation(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.evaluate(CANDIDATE_PROFILE, JOB_PROFILE)

        assert isinstance(result, RecruiterEvaluation)
        assert result.match_level == "good_match"
        assert result.hiring_confidence == 72
        assert result.interview_probability == 78
        assert len(result.strengths) == 4
        assert len(result.gaps) == 2
        assert "phone screen" in result.verdict
        assert len(result.reasoning) >= 3
        mock_client.generate_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_unwraps_single_key_response(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = {"evaluation": VALID_LLM_RESPONSE}

        agent = _make_agent(mock_client)
        result = await agent.evaluate(CANDIDATE_PROFILE, JOB_PROFILE)

        assert isinstance(result, RecruiterEvaluation)
        assert result.match_level == "good_match"

    @pytest.mark.asyncio
    async def test_retries_on_parse_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            LLMParseError("bad json"),
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        result = await agent.evaluate(CANDIDATE_PROFILE, JOB_PROFILE)

        assert isinstance(result, RecruiterEvaluation)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_validation_error(self) -> None:
        mock_client = AsyncMock()
        # First response has invalid structure
        mock_client.generate_json.side_effect = [
            {"hiring_confidence": "not_a_number_at_all", "strengths": "not_a_list"},
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        result = await agent.evaluate(CANDIDATE_PROFILE, JOB_PROFILE)

        assert isinstance(result, RecruiterEvaluation)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("always bad")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(RecruiterAgentError, match="after 3 attempt"):
            await agent.evaluate(CANDIDATE_PROFILE, JOB_PROFILE)

        assert mock_client.generate_json.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_immediately_on_api_error(self) -> None:
        from services.llm import LLMAPIError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMAPIError("quota exceeded")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(LLMAPIError):
            await agent.evaluate(CANDIDATE_PROFILE, JOB_PROFILE)

        assert mock_client.generate_json.call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_clamped_to_minimum_1(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client, max_retries=0)
        assert agent._max_retries == 1

        result = await agent.evaluate(CANDIDATE_PROFILE, JOB_PROFILE)
        assert isinstance(result, RecruiterEvaluation)

    @pytest.mark.asyncio
    async def test_prompt_includes_candidate_and_job_data(self) -> None:
        """Verify the prompt contains serialized candidate and job data."""
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        await agent.evaluate(CANDIDATE_PROFILE, JOB_PROFILE)

        call_args = mock_client.generate_json.call_args[0][0]
        # Prompt should contain candidate skills and job role
        assert "Python" in call_args
        assert "Senior Backend Engineer" in call_args
        assert "Kubernetes" in call_args


# ---------------------------------------------------------------------------
# Tests — run() (pipeline interface)
# ---------------------------------------------------------------------------


class TestRecruiterAgentRun:
    @pytest.mark.asyncio
    async def test_run_returns_evaluation_in_context(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.run({
            "candidate_profile": CANDIDATE_PROFILE,
            "job_profile": JOB_PROFILE,
        })

        assert "recruiter_evaluation" in result
        assert isinstance(result["recruiter_evaluation"], RecruiterEvaluation)

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_candidate(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({"job_profile": JOB_PROFILE})

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_job(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({"candidate_profile": CANDIDATE_PROFILE})

    @pytest.mark.asyncio
    async def test_run_propagates_agent_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("bad")

        agent = _make_agent(mock_client, max_retries=1)
        with pytest.raises(RecruiterAgentError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "job_profile": JOB_PROFILE,
            })
