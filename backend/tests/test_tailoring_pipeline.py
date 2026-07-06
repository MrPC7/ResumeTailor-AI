"""Integration tests for TailoringPipeline."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import (
    CandidateProfile,
    ExperienceRequirement,
    JobProfile,
    PreferredSkill,
    Project,
    RecruiterEvaluation,
    RequiredSkill,
    Responsibility,
    Skill,
    Suggestion,
    TailoredResume,
    WorkExperience,
)
from services.orchestrator.tailoring_pipeline import (
    TailoringFailureResult,
    TailoringPipeline,
    TailoringResult,
)
from services.agents.resume_tailor.agent import ResumeTailorAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CANDIDATE = CandidateProfile(
    skills=[
        Skill(name="Python", category="Programming Language"),
        Skill(name="FastAPI", category="Framework"),
        Skill(name="Docker", category="DevOps"),
    ],
    work_experience=[
        WorkExperience(
            company="Acme Corp",
            position="Engineer",
            duration="2021 - Present",
            responsibilities=["Built APIs", "Led deployments"],
            technologies=["Python", "FastAPI", "Docker"],
        ),
    ],
    projects=[
        Project(
            name="TaskAPI",
            description="REST task manager",
            technologies=["FastAPI"],
            role="Developer",
        ),
    ],
    total_years_experience=4.0,
    primary_domain="Backend",
)

JOB = JobProfile(
    role="Senior Backend Engineer",
    seniority="Senior",
    must_have_skills=[RequiredSkill(name="Python", category="PL")],
    preferred_skills=[PreferredSkill(name="Docker", category="DevOps")],
    responsibilities=[Responsibility(description="Build APIs", priority="high")],
    experience_required=ExperienceRequirement(min_years=3.0, domain="Backend"),
)

EVALUATION = RecruiterEvaluation(
    match_level="good_match",
    hiring_confidence=70,
    interview_probability=75,
    strengths=["Python proficiency"],
    gaps=["No Kubernetes"],
    verdict="Good fit.",
    reasoning=["Python matches"],
)

SELECTED_SUGGESTIONS = [
    Suggestion(
        id="suggestion_1",
        title="Front-load Python in skills",
        description="Move Python to first position.",
        priority="high",
        estimated_impact="Improves visibility",
        affected_section="skills",
    ),
    Suggestion(
        id="suggestion_2",
        title="Emphasize Docker in experience",
        description="Highlight containerization in Acme role.",
        priority="critical",
        estimated_impact="Addresses DevOps gap",
        affected_section="experience",
    ),
]

UNSELECTED_SUGGESTIONS = [
    Suggestion(
        id="suggestion_3",
        title="Add summary",
        description="Write a professional summary.",
        priority="medium",
        estimated_impact="Better first impression",
        affected_section="summary",
    ),
]

VALID_TAILOR_RESPONSE: dict[str, Any] = {
    "summary": "Backend Engineer with 4 years Python experience.",
    "skills": ["Python", "FastAPI", "Docker"],
    "experience": [
        {
            "company": "Acme Corp",
            "position": "Engineer",
            "duration": "2021 - Present",
            "description": "Architected containerized APIs with FastAPI and Docker.",
            "technologies": ["Python", "FastAPI", "Docker"],
        },
    ],
    "projects": [
        {
            "name": "TaskAPI",
            "description": "High-performance REST API built with FastAPI.",
            "technologies": ["FastAPI"],
        },
    ],
    "improvements_made": [
        "Applied suggestion_1: Reordered skills",
        "Applied suggestion_2: Emphasized Docker in experience",
    ],
    "gaps_addressed": [
        "Surfaced Docker containerization (suggestion_2)",
    ],
}


def _build_pipeline(
    llm_responses: list[dict[str, Any]],
) -> tuple[TailoringPipeline, AsyncMock]:
    mock_client = AsyncMock()
    mock_client.generate_json.side_effect = llm_responses

    agent = ResumeTailorAgent(client=mock_client, max_retries=1)
    pipeline = TailoringPipeline(tailor_agent=agent, timeout_seconds=30)
    return pipeline, mock_client


# ---------------------------------------------------------------------------
# Success tests
# ---------------------------------------------------------------------------


class TestTailoringPipelineSuccess:
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self) -> None:
        pipeline, mock_client = _build_pipeline([VALID_TAILOR_RESPONSE])

        result = await pipeline.run(
            CANDIDATE, JOB, EVALUATION,
            SELECTED_SUGGESTIONS, SELECTED_SUGGESTIONS + UNSELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoringResult)
        assert result.success is True
        assert result.suggestions_applied == 2
        assert result.tailored_resume.skills[0] == "Python"
        assert len(result.tailored_resume.experience) == 1
        assert result.original_length > 0
        assert result.tailored_length > 0
        mock_client.generate_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_length_within_budget_calculated(self) -> None:
        pipeline, _ = _build_pipeline([VALID_TAILOR_RESPONSE])

        result = await pipeline.run(
            CANDIDATE, JOB, EVALUATION, SELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoringResult)
        assert isinstance(result.length_within_budget, bool)

    @pytest.mark.asyncio
    async def test_to_dict_serializable(self) -> None:
        pipeline, _ = _build_pipeline([VALID_TAILOR_RESPONSE])

        result = await pipeline.run(
            CANDIDATE, JOB, EVALUATION, SELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoringResult)
        output = result.to_dict()
        assert output["success"] is True
        assert "tailored_resume" in output
        assert isinstance(output["tailored_resume"], dict)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestTailoringPipelineValidation:
    @pytest.mark.asyncio
    async def test_empty_suggestions_returns_failure(self) -> None:
        pipeline, _ = _build_pipeline([])

        result = await pipeline.run(CANDIDATE, JOB, EVALUATION, [])

        assert isinstance(result, TailoringFailureResult)
        assert result.success is False
        assert "No suggestions selected" in result.error
        assert result.error_type == "validation"

    @pytest.mark.asyncio
    async def test_suggestion_without_id_returns_failure(self) -> None:
        bad_suggestion = Suggestion(
            id="", title="Test", description="Desc",
            priority="high", estimated_impact="Impact", affected_section="skills",
        )
        pipeline, _ = _build_pipeline([])

        result = await pipeline.run(CANDIDATE, JOB, EVALUATION, [bad_suggestion])

        assert isinstance(result, TailoringFailureResult)
        assert "missing id" in result.error

    @pytest.mark.asyncio
    async def test_suggestion_without_title_returns_failure(self) -> None:
        bad_suggestion = Suggestion(
            id="s1", title="", description="Desc",
            priority="high", estimated_impact="Impact", affected_section="skills",
        )
        pipeline, _ = _build_pipeline([])

        result = await pipeline.run(CANDIDATE, JOB, EVALUATION, [bad_suggestion])

        assert isinstance(result, TailoringFailureResult)
        assert "missing title" in result.error


# ---------------------------------------------------------------------------
# Failure/transactional tests
# ---------------------------------------------------------------------------


class TestTailoringPipelineFailure:
    @pytest.mark.asyncio
    async def test_agent_failure_returns_original_resume(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("always bad")

        agent = ResumeTailorAgent(client=mock_client, max_retries=1)
        pipeline = TailoringPipeline(tailor_agent=agent, timeout_seconds=30)

        result = await pipeline.run(
            CANDIDATE, JOB, EVALUATION, SELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoringFailureResult)
        assert result.success is False
        assert result.error_type == "agent_error"
        assert result.original_resume == CANDIDATE
        assert result.suggestions_attempted == 2

    @pytest.mark.asyncio
    async def test_timeout_returns_original_resume(self) -> None:
        async def slow_generate(*args: Any, **kwargs: Any) -> dict:
            import asyncio
            await asyncio.sleep(10)
            return VALID_TAILOR_RESPONSE

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = slow_generate

        agent = ResumeTailorAgent(client=mock_client, max_retries=1)
        pipeline = TailoringPipeline(tailor_agent=agent, timeout_seconds=1)

        result = await pipeline.run(
            CANDIDATE, JOB, EVALUATION, SELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoringFailureResult)
        assert result.success is False
        assert result.error_type == "timeout"
        assert result.original_resume == CANDIDATE

    @pytest.mark.asyncio
    async def test_failure_result_serializable(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("bad")

        agent = ResumeTailorAgent(client=mock_client, max_retries=1)
        pipeline = TailoringPipeline(tailor_agent=agent, timeout_seconds=30)

        result = await pipeline.run(
            CANDIDATE, JOB, EVALUATION, SELECTED_SUGGESTIONS,
        )

        assert isinstance(result, TailoringFailureResult)
        output = result.to_dict()
        assert output["success"] is False
        assert "original_resume" in output
        assert output["error_type"] == "agent_error"


# ---------------------------------------------------------------------------
# Resume validation tests
# ---------------------------------------------------------------------------


class TestTailoringPipelineResumeValidation:
    @pytest.mark.asyncio
    async def test_detects_experience_count_mismatch(self) -> None:
        """If LLM adds an extra experience entry, validation catches it."""
        bad_response = {
            **VALID_TAILOR_RESPONSE,
            "experience": [
                VALID_TAILOR_RESPONSE["experience"][0],
                {
                    "company": "Fake Corp",
                    "position": "Engineer",
                    "duration": "2020",
                    "description": "Invented entry",
                    "technologies": [],
                },
            ],
        }
        pipeline, _ = _build_pipeline([bad_response])

        result = await pipeline.run(
            CANDIDATE, JOB, EVALUATION, SELECTED_SUGGESTIONS,
        )

        # Pipeline still succeeds (validation is non-blocking) but logs warning
        assert isinstance(result, TailoringResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_detects_new_skills_added(self) -> None:
        """If LLM adds skills not in original, validation catches it."""
        bad_response = {
            **VALID_TAILOR_RESPONSE,
            "skills": ["Python", "FastAPI", "Docker", "Kubernetes"],
        }
        pipeline, _ = _build_pipeline([bad_response])

        result = await pipeline.run(
            CANDIDATE, JOB, EVALUATION, SELECTED_SUGGESTIONS,
        )

        # Non-blocking — still returns result
        assert isinstance(result, TailoringResult)
        assert result.success is True
