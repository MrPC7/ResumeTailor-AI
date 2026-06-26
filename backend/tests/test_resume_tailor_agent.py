"""Unit tests for ResumeTailorAgent."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    TailoredResume,
    Skill,
    WorkExperience,
    Project,
    RequiredSkill,
    PreferredSkill,
    Responsibility,
    ExperienceRequirement,
)
from services.agents.resume_tailor.agent import (
    ResumeTailorAgent,
    ResumeTailorAgentError,
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
        RequiredSkill(name="Kubernetes", category="DevOps"),
    ],
    preferred_skills=[
        PreferredSkill(name="AWS", category="Cloud"),
    ],
    responsibilities=[
        Responsibility(description="Design scalable APIs", priority="high"),
        Responsibility(description="Mentor junior engineers", priority="medium"),
    ],
    experience_required=ExperienceRequirement(
        min_years=5.0, max_years=None, domain="Backend Development"
    ),
)

RECRUITER_EVALUATION = RecruiterEvaluation(
    match_level="good_match",
    hiring_confidence=72,
    interview_probability=78,
    strengths=[
        "Strong Python + FastAPI proficiency demonstrated at Acme Corp",
        "Docker experience with real deployment evidence",
        "AWS migration leadership shows cloud capability",
    ],
    gaps=[
        "No Kubernetes experience mentioned — must-have requirement",
        "No explicit mentoring evidence for Senior role",
    ],
    verdict="Good fit with one DevOps gap; recommend phone screen.",
    reasoning=[
        "Python and FastAPI match well",
        "Missing Kubernetes reduces confidence",
        "AWS is preferred skill bonus",
    ],
)

VALID_LLM_RESPONSE: dict[str, Any] = {
    "summary": "Senior Backend Engineer with 5 years building scalable Python microservices. Proven track record with FastAPI, Docker containerization, and AWS cloud infrastructure.",
    "skills": [
        "Python", "FastAPI", "Docker", "AWS", "PostgreSQL", "Redis",
    ],
    "experience": [
        {
            "company": "Acme Corp",
            "position": "Senior Backend Engineer",
            "duration": "Jan 2021 - Present",
            "description": "Architected and deployed containerized microservices using FastAPI and Docker. Led AWS infrastructure migration reducing deployment time by 40%.",
            "technologies": ["Python", "FastAPI", "Docker", "AWS"],
        },
        {
            "company": "StartupXYZ",
            "position": "Software Engineer",
            "duration": "2019 - 2020",
            "description": "Developed high-performance REST APIs serving 10k+ requests/sec. Implemented CI/CD pipelines improving release velocity.",
            "technologies": ["Python", "Flask", "PostgreSQL"],
        },
    ],
    "projects": [
        {
            "name": "ResumeTailor",
            "description": "Built AI-powered resume optimization platform with FastAPI backend and Docker-based deployment pipeline.",
            "technologies": ["FastAPI", "React", "Docker"],
        },
    ],
    "improvements_made": [
        "Reordered skills to front-load Python, FastAPI, Docker as must-have requirements",
        "Rewrote Acme Corp description to emphasize containerization and cloud migration",
        "Added professional summary targeting Senior Backend Engineer role",
        "Highlighted Docker usage across multiple entries for DevOps visibility",
    ],
    "gaps_addressed": [
        "Surfaced Docker containerization experience to partially address DevOps/infrastructure gap",
        "Emphasized AWS migration leadership to strengthen cloud capability narrative",
    ],
}


def _make_agent(mock_client: AsyncMock, max_retries: int = 2) -> ResumeTailorAgent:
    return ResumeTailorAgent(client=mock_client, max_retries=max_retries)


# ---------------------------------------------------------------------------
# Tests — tailor()
# ---------------------------------------------------------------------------


class TestResumeTailorAgentTailor:
    @pytest.mark.asyncio
    async def test_successful_tailoring(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.tailor(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert isinstance(result, TailoredResume)
        assert "Senior Backend Engineer" in result.summary
        assert len(result.skills) == 6
        assert result.skills[0] == "Python"
        assert len(result.experience) == 2
        assert result.experience[0].company == "Acme Corp"
        assert len(result.projects) == 1
        assert result.projects[0].name == "ResumeTailor"
        assert len(result.improvements_made) >= 3
        assert len(result.gaps_addressed) >= 1
        mock_client.generate_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_unwraps_single_key_response(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = {"tailored": VALID_LLM_RESPONSE}

        agent = _make_agent(mock_client)
        result = await agent.tailor(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert isinstance(result, TailoredResume)
        assert len(result.experience) == 2

    @pytest.mark.asyncio
    async def test_retries_on_parse_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            LLMParseError("bad json"),
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        result = await agent.tailor(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert isinstance(result, TailoredResume)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_validation_error(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            {"experience": "not_a_list"},
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        result = await agent.tailor(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert isinstance(result, TailoredResume)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("always bad")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(ResumeTailorAgentError, match="after 3 attempt"):
            await agent.tailor(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert mock_client.generate_json.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_immediately_on_api_error(self) -> None:
        from services.llm import LLMAPIError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMAPIError("quota exceeded")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(LLMAPIError):
            await agent.tailor(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert mock_client.generate_json.call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_clamped_to_minimum_1(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client, max_retries=0)
        assert agent._max_retries == 1

    @pytest.mark.asyncio
    async def test_prompt_includes_all_three_inputs(self) -> None:
        """Verify the prompt contains candidate, job, and evaluation data."""
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        await agent.tailor(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        call_args = mock_client.generate_json.call_args[0][0]
        # Candidate data
        assert "Python" in call_args
        assert "Acme Corp" in call_args
        # Job data
        assert "Senior Backend Engineer" in call_args
        assert "Kubernetes" in call_args
        # Evaluation data
        assert "good_match" in call_args
        assert "No Kubernetes experience" in call_args


# ---------------------------------------------------------------------------
# Tests — run() (pipeline interface)
# ---------------------------------------------------------------------------


class TestResumeTailorAgentRun:
    @pytest.mark.asyncio
    async def test_run_returns_tailored_resume_in_context(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.run({
            "candidate_profile": CANDIDATE_PROFILE,
            "job_profile": JOB_PROFILE,
            "recruiter_evaluation": RECRUITER_EVALUATION,
        })

        assert "tailored_resume" in result
        assert isinstance(result["tailored_resume"], TailoredResume)

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_candidate(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({
                "job_profile": JOB_PROFILE,
                "recruiter_evaluation": RECRUITER_EVALUATION,
            })

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_job(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "recruiter_evaluation": RECRUITER_EVALUATION,
            })

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_evaluation(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "job_profile": JOB_PROFILE,
            })

    @pytest.mark.asyncio
    async def test_run_propagates_agent_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("bad")

        agent = _make_agent(mock_client, max_retries=1)
        with pytest.raises(ResumeTailorAgentError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "job_profile": JOB_PROFILE,
                "recruiter_evaluation": RECRUITER_EVALUATION,
            })
