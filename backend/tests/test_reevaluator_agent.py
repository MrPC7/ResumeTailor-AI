"""Unit tests for ReevaluatorAgent."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import (
    CandidateProfile,
    ImprovementMetrics,
    JobProfile,
    RecruiterEvaluation,
    ReevaluationResult,
    TailoredResume,
    TailoredExperience,
    TailoredProject,
    Skill,
    WorkExperience,
    Project,
    Education,
    RequiredSkill,
    PreferredSkill,
    Responsibility,
    ExperienceRequirement,
)
from services.agents.reevaluator.agent import (
    ReevaluatorAgent,
    ReevaluatorAgentError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CANDIDATE_PROFILE = CandidateProfile(
    skills=[
        Skill(name="Python", category="Programming Language"),
        Skill(name="FastAPI", category="Framework"),
        Skill(name="Docker", category="DevOps"),
        Skill(name="PostgreSQL", category="Database"),
    ],
    work_experience=[
        WorkExperience(
            company="Acme Corp",
            position="Senior Engineer",
            duration="2021 - Present",
            responsibilities=["Built APIs", "Led deployments"],
            technologies=["Python", "FastAPI", "Docker"],
        ),
    ],
    education=[Education(institution="MIT", degree="B.S.", field_of_study="CS", year="2020")],
    projects=[
        Project(
            name="TaskAPI",
            description="REST task manager",
            technologies=["FastAPI", "PostgreSQL"],
            role="Developer",
        ),
    ],
    total_years_experience=4.0,
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
    responsibilities=[Responsibility(description="Design APIs", priority="high")],
    experience_required=ExperienceRequirement(min_years=5.0, domain="Backend"),
)

BEFORE_EVALUATION = RecruiterEvaluation(
    match_level="partial_match",
    hiring_confidence=55,
    interview_probability=50,
    strengths=[
        "Strong Python + FastAPI skills",
        "Docker experience",
    ],
    gaps=[
        "No Kubernetes experience",
        "4 years vs 5 years required",
        "No mentoring evidence",
    ],
    verdict="Partial fit; borderline phone screen.",
    reasoning=["Python matches", "Missing Kubernetes", "Slightly underexperienced"],
)

TAILORED_RESUME = TailoredResume(
    summary="Senior Backend Engineer with 4 years building scalable Python microservices.",
    skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
    experience=[
        TailoredExperience(
            company="Acme Corp",
            position="Senior Engineer",
            duration="2021 - Present",
            description="Architected containerized microservices with FastAPI and Docker. Managed CI/CD pipelines for cloud deployments.",
            technologies=["Python", "FastAPI", "Docker"],
        ),
    ],
    projects=[
        TailoredProject(
            name="TaskAPI",
            description="High-performance REST API built with FastAPI and PostgreSQL, serving production traffic.",
            technologies=["FastAPI", "PostgreSQL"],
        ),
    ],
    improvements_made=["Emphasized containerization", "Highlighted API design"],
    gaps_addressed=["Surfaced Docker for DevOps visibility"],
)

# Simulated "after" LLM response (recruiter evaluating the tailored resume)
AFTER_EVAL_LLM_RESPONSE: dict[str, Any] = {
    "match_level": "good_match",
    "hiring_confidence": 68,
    "interview_probability": 72,
    "strengths": [
        "Strong Python + FastAPI proficiency",
        "Docker containerization clearly demonstrated",
        "API architecture expertise evident",
    ],
    "gaps": [
        "No Kubernetes experience — still a must-have gap",
        "4 years vs 5 years required",
    ],
    "verdict": "Improved fit; recommend phone screen.",
    "reasoning": [
        "Python and FastAPI match strongly",
        "Docker experience now clearly visible",
        "Still missing Kubernetes",
        "Experience years slightly short",
    ],
}


def _make_agent(mock_client: AsyncMock, max_retries: int = 2) -> ReevaluatorAgent:
    return ReevaluatorAgent(client=mock_client, max_retries=max_retries)


# ---------------------------------------------------------------------------
# Tests — reevaluate()
# ---------------------------------------------------------------------------


class TestReevaluatorAgentReevaluate:
    @pytest.mark.asyncio
    async def test_successful_reevaluation(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = AFTER_EVAL_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.reevaluate(
            CANDIDATE_PROFILE, JOB_PROFILE, TAILORED_RESUME, BEFORE_EVALUATION
        )

        assert isinstance(result, ReevaluationResult)

        # Before should be the original evaluation
        assert result.before.hiring_confidence == 55
        assert result.before.match_level == "partial_match"

        # After should be the new evaluation
        assert result.after.hiring_confidence == 68
        assert result.after.match_level == "good_match"

        # Improvement metrics
        assert result.improvement.hiring_confidence_delta == 13
        assert result.improvement.interview_probability_delta == 22
        assert result.improvement.gaps_before == 3
        assert result.improvement.gaps_after == 2
        assert result.improvement.gaps_reduced == 1
        assert result.improvement.strengths_before == 2
        assert result.improvement.strengths_after == 3
        assert result.improvement.strengths_gained == 1
        assert result.improvement.match_level_before == "partial_match"
        assert result.improvement.match_level_after == "good_match"
        assert result.improvement.improved is True

    @pytest.mark.asyncio
    async def test_no_improvement_scenario(self) -> None:
        """When tailored resume scores the same or lower."""
        same_eval_response = {
            "match_level": "partial_match",
            "hiring_confidence": 50,
            "interview_probability": 45,
            "strengths": ["Python skills"],
            "gaps": ["No Kubernetes", "Underexperienced", "No mentoring"],
            "verdict": "No improvement.",
            "reasoning": ["Same gaps remain"],
        }
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = same_eval_response

        agent = _make_agent(mock_client)
        result = await agent.reevaluate(
            CANDIDATE_PROFILE, JOB_PROFILE, TAILORED_RESUME, BEFORE_EVALUATION
        )

        assert result.improvement.hiring_confidence_delta == -5
        assert result.improvement.improved is False

    @pytest.mark.asyncio
    async def test_raises_on_recruiter_failure(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("always bad")

        agent = _make_agent(mock_client, max_retries=1)
        with pytest.raises(ReevaluatorAgentError, match="Failed to evaluate"):
            await agent.reevaluate(
                CANDIDATE_PROFILE, JOB_PROFILE, TAILORED_RESUME, BEFORE_EVALUATION
            )

    @pytest.mark.asyncio
    async def test_tailored_profile_preserves_education(self) -> None:
        """Education from original profile should carry over to tailored profile."""
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = AFTER_EVAL_LLM_RESPONSE

        agent = _make_agent(mock_client)
        tailored_profile = agent._build_tailored_profile(CANDIDATE_PROFILE, TAILORED_RESUME)

        assert len(tailored_profile.education) == 1
        assert tailored_profile.education[0].institution == "MIT"

    @pytest.mark.asyncio
    async def test_tailored_profile_uses_tailored_skills(self) -> None:
        """Skills in tailored profile come from TailoredResume."""
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)
        tailored_profile = agent._build_tailored_profile(CANDIDATE_PROFILE, TAILORED_RESUME)

        skill_names = [s.name for s in tailored_profile.skills]
        assert skill_names == ["Python", "FastAPI", "Docker", "PostgreSQL"]

    @pytest.mark.asyncio
    async def test_tailored_profile_uses_tailored_experience(self) -> None:
        """Experience in tailored profile uses rewritten descriptions."""
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)
        tailored_profile = agent._build_tailored_profile(CANDIDATE_PROFILE, TAILORED_RESUME)

        assert len(tailored_profile.work_experience) == 1
        assert tailored_profile.work_experience[0].company == "Acme Corp"
        assert "containerized" in tailored_profile.work_experience[0].responsibilities[0]

    @pytest.mark.asyncio
    async def test_prompt_contains_tailored_content(self) -> None:
        """RecruiterAgent prompt should contain the tailored resume content."""
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = AFTER_EVAL_LLM_RESPONSE

        agent = _make_agent(mock_client)
        await agent.reevaluate(
            CANDIDATE_PROFILE, JOB_PROFILE, TAILORED_RESUME, BEFORE_EVALUATION
        )

        call_args = mock_client.generate_json.call_args[0][0]
        assert "containerized" in call_args
        assert "Senior Backend Engineer" in call_args


# ---------------------------------------------------------------------------
# Tests — run() (pipeline interface)
# ---------------------------------------------------------------------------


class TestReevaluatorAgentRun:
    @pytest.mark.asyncio
    async def test_run_returns_reevaluation_result(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = AFTER_EVAL_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.run({
            "candidate_profile": CANDIDATE_PROFILE,
            "job_profile": JOB_PROFILE,
            "tailored_resume": TAILORED_RESUME,
            "recruiter_evaluation": BEFORE_EVALUATION,
        })

        assert "reevaluation_result" in result
        assert isinstance(result["reevaluation_result"], ReevaluationResult)

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_tailored(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "job_profile": JOB_PROFILE,
                "recruiter_evaluation": BEFORE_EVALUATION,
            })

    @pytest.mark.asyncio
    async def test_run_raises_key_error_without_before_eval(self) -> None:
        mock_client = AsyncMock()
        agent = _make_agent(mock_client)

        with pytest.raises(KeyError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "job_profile": JOB_PROFILE,
                "tailored_resume": TAILORED_RESUME,
            })

    @pytest.mark.asyncio
    async def test_run_propagates_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("bad")

        agent = _make_agent(mock_client, max_retries=1)
        with pytest.raises(ReevaluatorAgentError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "job_profile": JOB_PROFILE,
                "tailored_resume": TAILORED_RESUME,
                "recruiter_evaluation": BEFORE_EVALUATION,
            })


# ---------------------------------------------------------------------------
# Tests — ImprovementMetrics deterministic computation
# ---------------------------------------------------------------------------


class TestImprovementMetrics:
    def test_positive_improvement(self) -> None:
        metrics = ImprovementMetrics(
            hiring_confidence_delta=15,
            interview_probability_delta=20,
            gaps_before=3,
            gaps_after=1,
            gaps_reduced=2,
            strengths_before=2,
            strengths_after=4,
            strengths_gained=2,
            match_level_before="partial_match",
            match_level_after="good_match",
            improved=True,
        )
        assert metrics.improved is True
        assert metrics.gaps_reduced == 2
        assert metrics.strengths_gained == 2

    def test_negative_improvement(self) -> None:
        metrics = ImprovementMetrics(
            hiring_confidence_delta=-5,
            interview_probability_delta=-10,
            gaps_before=2,
            gaps_after=3,
            gaps_reduced=-1,
            strengths_before=3,
            strengths_after=2,
            strengths_gained=-1,
            match_level_before="good_match",
            match_level_after="partial_match",
            improved=False,
        )
        assert metrics.improved is False
        assert metrics.hiring_confidence_delta == -5

    def test_defaults(self) -> None:
        metrics = ImprovementMetrics()
        assert metrics.hiring_confidence_delta == 0
        assert metrics.improved is False
