"""Unit tests for SuggestionGeneratorAgent."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    Suggestion,
    SuggestionReport,
    Skill,
    WorkExperience,
    Project,
    RequiredSkill,
    PreferredSkill,
    Responsibility,
    ExperienceRequirement,
)
from services.agents.suggestion_generator.agent import (
    SuggestionGeneratorAgent,
    SuggestionGeneratorError,
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
            position="Backend Engineer",
            duration="2021 - Present",
            responsibilities=["Built APIs", "Managed deployments"],
            technologies=["Python", "FastAPI", "Docker"],
        ),
    ],
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
    preferred_skills=[
        PreferredSkill(name="AWS", category="Cloud"),
    ],
    responsibilities=[
        Responsibility(description="Design scalable APIs", priority="high"),
        Responsibility(description="Mentor juniors", priority="medium"),
    ],
    experience_required=ExperienceRequirement(
        min_years=5.0, max_years=None, domain="Backend Development"
    ),
)

RECRUITER_EVALUATION = RecruiterEvaluation(
    match_level="partial_match",
    hiring_confidence=55,
    interview_probability=50,
    strengths=[
        "Strong Python + FastAPI skills",
        "Docker containerization experience",
    ],
    gaps=[
        "No Kubernetes experience — must-have requirement",
        "4 years vs 5 years required",
        "No mentoring evidence for Senior role",
    ],
    verdict="Partial fit; borderline.",
    reasoning=["Python matches", "Missing Kubernetes", "Slightly underexperienced"],
)

VALID_LLM_RESPONSE: dict[str, Any] = {
    "suggestions": [
        {
            "id": "suggestion_1",
            "title": "Highlight container orchestration experience",
            "description": "Your Docker experience at Acme Corp demonstrates containerization skills. Reword your experience description to emphasize orchestration patterns (multi-container, networking, scaling) which partially bridges the Kubernetes gap.",
            "priority": "critical",
            "estimated_impact": "Addresses primary recruiter gap — could improve match from partial to good",
            "affected_section": "experience",
        },
        {
            "id": "suggestion_2",
            "title": "Front-load Python and FastAPI in skills",
            "description": "Move Python and FastAPI to the first positions in your skills list. These are must-have requirements and should be immediately visible to ATS and recruiter scans.",
            "priority": "high",
            "estimated_impact": "Improves keyword visibility and first-impression scan time",
            "affected_section": "skills",
        },
        {
            "id": "suggestion_3",
            "title": "Add leadership narrative to experience",
            "description": "The recruiter identified 'no mentoring evidence' as a gap for the Senior role. If you have any code review, onboarding, or team collaboration experience at Acme Corp, surface it in your experience description.",
            "priority": "high",
            "estimated_impact": "Addresses Senior-level expectation — could improve interview probability by 10-15 points",
            "affected_section": "experience",
        },
        {
            "id": "suggestion_4",
            "title": "Rewrite summary targeting Senior Backend role",
            "description": "Add or update your professional summary to explicitly target 'Senior Backend Engineer' with emphasis on API architecture, containerization, and your 4 years of relevant experience.",
            "priority": "medium",
            "estimated_impact": "Improves recruiter first-impression alignment",
            "affected_section": "summary",
        },
        {
            "id": "suggestion_5",
            "title": "Emphasize API design in TaskAPI project",
            "description": "The job requires 'Design scalable APIs' as a high-priority responsibility. Rewrite your TaskAPI project description to highlight scalability aspects (performance, load handling) rather than just 'REST task manager'.",
            "priority": "medium",
            "estimated_impact": "Strengthens evidence for core job responsibility",
            "affected_section": "projects",
        },
    ],
    "total_count": 5,
    "critical_count": 1,
    "high_count": 2,
}


def _make_agent(mock_client: AsyncMock, max_retries: int = 2) -> SuggestionGeneratorAgent:
    return SuggestionGeneratorAgent(client=mock_client, max_retries=max_retries)


# ---------------------------------------------------------------------------
# Tests — generate()
# ---------------------------------------------------------------------------


class TestSuggestionGeneratorAgentGenerate:
    @pytest.mark.asyncio
    async def test_successful_generation(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        report = await agent.generate(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert isinstance(report, SuggestionReport)
        assert report.total_count == 5
        assert report.critical_count == 1
        assert report.high_count == 2
        assert len(report.suggestions) == 5

        # Verify first suggestion structure
        s1 = report.suggestions[0]
        assert s1.id == "suggestion_1"
        assert s1.priority == "critical"
        assert s1.affected_section == "experience"
        assert "container" in s1.title.lower()
        mock_client.generate_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_unwraps_single_key_response(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = {"report": VALID_LLM_RESPONSE}

        agent = _make_agent(mock_client)
        report = await agent.generate(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert isinstance(report, SuggestionReport)
        assert len(report.suggestions) == 5

    @pytest.mark.asyncio
    async def test_retries_on_parse_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            LLMParseError("bad json"),
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        report = await agent.generate(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert isinstance(report, SuggestionReport)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_validation_error(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            {"suggestions": "not_a_list"},
            VALID_LLM_RESPONSE,
        ]

        agent = _make_agent(mock_client, max_retries=2)
        report = await agent.generate(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert isinstance(report, SuggestionReport)
        assert mock_client.generate_json.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("always bad")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(SuggestionGeneratorError, match="after 3 attempt"):
            await agent.generate(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert mock_client.generate_json.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_immediately_on_api_error(self) -> None:
        from services.llm import LLMAPIError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMAPIError("quota exceeded")

        agent = _make_agent(mock_client, max_retries=3)
        with pytest.raises(LLMAPIError):
            await agent.generate(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        assert mock_client.generate_json.call_count == 1

    @pytest.mark.asyncio
    async def test_prompt_includes_all_three_inputs(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        await agent.generate(CANDIDATE_PROFILE, JOB_PROFILE, RECRUITER_EVALUATION)

        prompt = mock_client.generate_json.call_args[0][0]
        assert "Python" in prompt
        assert "Kubernetes" in prompt
        assert "partial_match" in prompt
        assert "No Kubernetes experience" in prompt


# ---------------------------------------------------------------------------
# Tests — run() (pipeline interface)
# ---------------------------------------------------------------------------


class TestSuggestionGeneratorAgentRun:
    @pytest.mark.asyncio
    async def test_run_returns_suggestion_report(self) -> None:
        mock_client = AsyncMock()
        mock_client.generate_json.return_value = VALID_LLM_RESPONSE

        agent = _make_agent(mock_client)
        result = await agent.run({
            "candidate_profile": CANDIDATE_PROFILE,
            "job_profile": JOB_PROFILE,
            "recruiter_evaluation": RECRUITER_EVALUATION,
        })

        assert "suggestion_report" in result
        assert isinstance(result["suggestion_report"], SuggestionReport)

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
    async def test_run_propagates_error(self) -> None:
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("bad")

        agent = _make_agent(mock_client, max_retries=1)
        with pytest.raises(SuggestionGeneratorError):
            await agent.run({
                "candidate_profile": CANDIDATE_PROFILE,
                "job_profile": JOB_PROFILE,
                "recruiter_evaluation": RECRUITER_EVALUATION,
            })


# ---------------------------------------------------------------------------
# Tests — Suggestion schema validation
# ---------------------------------------------------------------------------


class TestSuggestionSchema:
    def test_valid_suggestion(self) -> None:
        s = Suggestion.model_validate({
            "id": "suggestion_1",
            "title": "Front-load Python",
            "description": "Move Python to first position",
            "priority": "high",
            "estimated_impact": "Improves visibility",
            "affected_section": "skills",
        })
        assert s.id == "suggestion_1"
        assert s.priority == "high"
        assert s.affected_section == "skills"

    def test_priority_normalization(self) -> None:
        s = Suggestion.model_validate({"priority": "HIGH"})
        assert s.priority == "high"

    def test_invalid_priority_defaults_to_medium(self) -> None:
        s = Suggestion.model_validate({"priority": "urgent"})
        assert s.priority == "medium"

    def test_affected_section_valid(self) -> None:
        for section in ["summary", "skills", "experience", "projects", "education", "certifications"]:
            s = Suggestion.model_validate({"affected_section": section})
            assert s.affected_section == section

    def test_affected_section_unknown_passes_through(self) -> None:
        s = Suggestion.model_validate({"affected_section": "hobbies"})
        assert s.affected_section == "hobbies"

    def test_defaults(self) -> None:
        s = Suggestion.model_validate({})
        assert s.id == ""
        assert s.priority == ""

    def test_report_defaults(self) -> None:
        report = SuggestionReport.model_validate({})
        assert report.suggestions == []
        assert report.total_count == 0
        assert report.critical_count == 0
        assert report.high_count == 0

    def test_report_count_coercion(self) -> None:
        report = SuggestionReport.model_validate({
            "total_count": "5",
            "critical_count": 1.5,
            "high_count": -3,
        })
        assert report.total_count == 5
        assert report.critical_count == 1
        assert report.high_count == 0
