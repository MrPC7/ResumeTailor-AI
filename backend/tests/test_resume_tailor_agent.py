"""Unit tests for ResumeTailorAgent (with selected suggestions)."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    Suggestion,
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
    preferred_skills=[PreferredSkill(name="AWS", category="Cloud")],
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
    ],
    gaps=[
        "No Kubernetes experience mentioned — must-have requirement",
        "No explicit mentoring evidence for Senior role",
    ],
    verdict="Good fit with one DevOps gap; recommend phone screen.",
    reasoning=["Python matches", "Missing Kubernetes reduces confidence"],
)

SELECTED_SUGGESTIONS = [
    Suggestion(
        id="suggestion_1",
        title="Front-load Python and FastAPI in skills",
        description="Move Python and FastAPI to first positions in skills list.",
        priority="high",
        estimated_impact="Improves ATS keyword visibility",
        affected_section="skills",
    ),
    Suggestion(
        id="suggestion_3",
        title="Emphasize containerization in experience",
        description="Rewrite Acme Corp description to highlight Docker containerization.",
        priority="critical",
        estimated_impact="Partially addresses Kubernetes gap",
        affected_section="experience",
    ),
]

UNSELECTED_SUGGESTIONS = [
    Suggestion(
        id="suggestion_2",
        title="Add leadership narrative",
        description="Surface mentoring experience if any.",
        priority="high",
        estimated_impact="Addresses Senior role gap",
        affected_section="experience",
    ),
]

VALID_LLM_RESPONSE: dict[str, Any] = {
    "summary": "Senior Backend Engineer with 5 years building scalable Python microservices. Proven expertise with FastAPI and Docker containerization.",
    "skills": ["Python", "FastAPI", "Docker", "AWS", "PostgreSQL", "Redis"],
    "experience": [
        {
            "company": "Acme Corp",
            "position": "Senior Backend Engineer",
            "duration": "Jan 2021 - Present",
            "description": "Architected containerized microservices using FastAPI and Docker. Led AWS cloud migration reducing deployment overhead.",
            "technologies": ["Python", "FastAPI", "Docker", "AWS"],
        },
        {
            "company": "StartupXYZ",
            "position": "Software Engineer",
            "duration": "2019 - 2020",
            "description": "Developed REST APIs with Flask. Implemented CI/CD pipelines.",
            "technologies": ["Python", "Flask", "PostgreSQL"],
        },
    ],
    "projects": [
        {
            "name": "ResumeTailor",
            "description": "AI-powered resume optimization platform with FastAPI backend and Docker deployment.",
            "technologies": ["FastAPI", "React", "Docker"],
        },
    ],
    "improvements_made": [
        "Applied suggestion_1: Reordered skills to front-load Python and FastAPI",
        "Applied suggestion_3: Rewrote Acme Corp description to emphasize Docker containerization",
    ],
    "gaps_addressed": [
        "Surfaced Docker containerization to partially address DevOps gap (suggestion_3)",
    ],
}


def _make_agent(mock_client: AsyncMock, max_retries: int = 2) -> ResumeTailorAgent:
    return ResumeTailorAgent(client=mock_client, max_retries=max_retries)


# ---------------------------------------------------------------------------
# Tests — tailor()
# ---------------------------------------------------------------------------


class TestResumeTailorAgentTailor:
    @pytest.mark.asyncio
    async def test_successful_tailoring_with_suggestions(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.tailor(
            CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
            SELECTED_SUGGESTIONS, UNSELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoredResume)
        assert "Senior Backend Engineer" in result.summary
        assert result.skills[0] == "Python"
        assert result.skills[1] == "FastAPI"
        assert len(result.experience) == 2
        assert len(result.improvements_made) >= 2
        mock_client.generate_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_prompt_contains_selected_suggestions(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        await agent.tailor(
            CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
            SELECTED_SUGGESTIONS, UNSELECTED_SUGGESTIONS,
        )

        prompt = mock_client.generate_json.call_args[0][0]
        # Selected suggestions should be in prompt
        assert "suggestion_1" in prompt
        assert "suggestion_3" in prompt
        assert "Front-load Python" in prompt
        assert "Emphasize containerization" in prompt

    @pytest.mark.asyncio
    async def test_prompt_contains_unselected_suggestions(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        await agent.tailor(
            CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
            SELECTED_SUGGESTIONS, UNSELECTED_SUGGESTIONS,
        )

        prompt = mock_client.generate_json.call_args[0][0]
        # Unselected should also be in prompt (so LLM knows NOT to apply them)
        assert "suggestion_2" in prompt
        assert "Add leadership narrative" in prompt

    @pytest.mark.asyncio
    async def test_works_with_empty_unselected(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.tailor(
            CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
            SELECTED_SUGGESTIONS, [],
        )

        assert isinstance(result, TailoredResume)

    @pytest.mark.asyncio
    async def test_works_with_none_unselected(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.tailor(
            CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
            SELECTED_SUGGESTIONS, None,
        )

        assert isinstance(result, TailoredResume)

    @pytest.mark.asyncio
    async def test_unwraps_single_key_response(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = {"tailored": VALID_LLM_RESPONSE}

        agent = _make_agent(mock_client)
        result = await agent.tailor(
            CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
            SELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoredResume)

    @pytest.mark.asyncio
    async def test_retries_on_parse_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            LLMParseError("bad json"),
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        result = await agent.tailor(
            CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
            SELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoredResume)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("always bad")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(ResumeTailorAgentError, match="after 3 attempt"):
            await agent.tailor(
                CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
                SELECTED_SUGGESTIONS,
            )

        assert mock_client.generate_json.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_immediately_on_api_error(self) -> None:
        from services.llm import LLMAPIError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMAPIError("quota exceeded")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(LLMAPIError):
            await agent.tailor(
                CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION,
                SELECTED_SUGGESTIONS,
            )

        assert mock_client.generate_json.call_count == 1


# ---------------------------------------------------------------------------
# Tests — run() (pipeline interface)
# ---------------------------------------------------------------------------


class TestResumeTailorAgentRun:
    @pytest.mark.asyncio
    async def test_run_returns_tailored_resume(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.run({
            "candidate_profile": CANDIDATE_PROFILE,
            "job_profile": JOB_PROFILE,
            "recruiter_evaluation": RECRUITER_EVALUATION,
            "selected_suggestions": SELECTED_SUGGESTIONS,
            "all_suggestions": SELECTED_SUGGESTIONS + UNSELECTED_SUGGESTIONS,
        })

        assert "tailored_resume" in result
        assert isinstance(result["tailored_resume"], TailoredResume)

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_suggestions(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "job_profile": JOB_PROFILE,
                "recruiter_evaluation": RECRUITER_EVALUATION,
            })

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_candidate(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({
                "job_profile": JOB_PROFILE,
                "recruiter_evaluation": RECRUITER_EVALUATION,
                "selected_suggestions": SELECTED_SUGGESTIONS,
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
                "selected_suggestions": SELECTED_SUGGESTIONS,
            })

    @pytest.mark.asyncio
    async def test_run_without_all_suggestions_uses_empty_unselected(self) -> None:
        """When all_suggestions is not in context, unselected list is empty."""
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.run({
            "candidate_profile": CANDIDATE_PROFILE,
            "job_profile": JOB_PROFILE,
            "recruiter_evaluation": RECRUITER_EVALUATION,
            "selected_suggestions": SELECTED_SUGGESTIONS,
        })

        assert isinstance(result["tailored_resume"], TailoredResume)
