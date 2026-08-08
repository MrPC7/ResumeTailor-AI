"""Integration tests for EvaluationPipeline — tests the full 3-agent flow."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
)
from services.orchestrator.evaluation_pipeline import (
    EvaluationPipeline,
    EvaluationResult,
    PipelineError,
    PipelineInputError,
)


# ---------------------------------------------------------------------------
# LLM response fixtures (simulate what each agent's LLM call returns)
# ---------------------------------------------------------------------------

RESUME_ANALYZER_LLM_RESPONSE: dict[str, Any] = {
    "skills": [
        {"name": "Python", "category": "Programming Language"},
        {"name": "FastAPI", "category": "Framework"},
        {"name": "Docker", "category": "DevOps"},
        {"name": "PostgreSQL", "category": "Database"},
    ],
    "work_experience": [
        {
            "company": "Acme Corp",
            "position": "Backend Engineer",
            "duration": "2021 - Present",
            "responsibilities": ["Built APIs", "Led deployments"],
            "technologies": ["Python", "FastAPI", "Docker"],
        }
    ],
    "education": [
        {
            "institution": "MIT",
            "degree": "B.S.",
            "field_of_study": "Computer Science",
            "year": "2020",
        }
    ],
    "projects": [
        {
            "name": "TaskAPI",
            "description": "REST task manager",
            "technologies": ["FastAPI", "PostgreSQL"],
            "role": "Solo developer",
        }
    ],
    "certifications": [],
    "total_years_experience": 4.0,
    "primary_domain": "Backend Development",
}

JD_ANALYZER_LLM_RESPONSE: dict[str, Any] = {
    "role": "Senior Backend Engineer",
    "seniority": "Senior",
    "must_have_skills": [
        {"name": "Python", "category": "Programming Language"},
        {"name": "FastAPI", "category": "Framework"},
        {"name": "Kubernetes", "category": "DevOps"},
    ],
    "preferred_skills": [
        {"name": "AWS", "category": "Cloud"},
    ],
    "responsibilities": [
        {"description": "Design scalable APIs", "priority": "high"},
        {"description": "Mentor juniors", "priority": "medium"},
    ],
    "experience_required": {
        "min_years": 5.0,
        "max_years": None,
        "domain": "Backend Development",
    },
}

RECRUITER_LLM_RESPONSE: dict[str, Any] = {
    "match_level": "partial_match",
    "hiring_confidence": 55,
    "interview_probability": 50,
    "strengths": [
        "Strong Python + FastAPI proficiency",
        "Real project evidence (TaskAPI) with FastAPI",
    ],
    "gaps": [
        "No Kubernetes experience — must-have",
        "4 years experience vs 5 years required",
    ],
    "verdict": "Partial fit — missing Kubernetes and slightly underexperienced; borderline phone screen.",
    "reasoning": [
        "2 of 3 must-have skills present (Python, FastAPI)",
        "Missing Kubernetes is critical — DevOps gap",
        "4 years vs 5 year minimum — slight shortfall",
        "Project evidence demonstrates practical FastAPI usage",
    ],
}

SAMPLE_RESUME = """\
John Doe — Backend Engineer
john@email.com | +1-555-0123

Experience:
Acme Corp — Backend Engineer (2021 - Present)
- Built REST APIs with FastAPI
- Led Docker-based deployments

Education:
MIT — B.S. Computer Science (2020)

Skills: Python, FastAPI, Docker, PostgreSQL

Projects:
TaskAPI — REST task manager built with FastAPI and PostgreSQL
"""

SAMPLE_JD = """\
Senior Backend Engineer — TechCo

Requirements:
- 5+ years backend experience
- Python and FastAPI required
- Kubernetes experience required

Nice to have:
- AWS experience

Responsibilities:
- Design and build scalable APIs
- Mentor junior developers
"""


# ---------------------------------------------------------------------------
# Helper: build pipeline with mocked LLM client
# ---------------------------------------------------------------------------


def _build_pipeline(
    llm_responses: list[dict[str, Any]],
) -> tuple[EvaluationPipeline, AsyncMock]:
    """Create pipeline with a mock LLM client that returns responses in order."""
    mock_client = AsyncMock()
    mock_client.generate_json.side_effect = llm_responses

    # Import agent classes directly to avoid singleton wiring
    from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
    from services.agents.jd_analyzer.agent import JDAnalyzerAgent
    from services.agents.recruiter.agent import RecruiterAgent

    pipeline = EvaluationPipeline(
        resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
        jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
        recruiter=RecruiterAgent(client=mock_client, max_retries=1),
    )
    return pipeline, mock_client


# ---------------------------------------------------------------------------
# Integration tests — full pipeline
# ---------------------------------------------------------------------------


class TestEvaluationPipelineIntegration:
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self) -> None:
        """Full pipeline produces correct EvaluationResult with all 3 agents."""
        pipeline, mock_client = _build_pipeline([
            RESUME_ANALYZER_LLM_RESPONSE,
            JD_ANALYZER_LLM_RESPONSE,
            RECRUITER_LLM_RESPONSE,
        ])

        result = await pipeline.run(
            raw_resume_text=SAMPLE_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        # Verify return type
        assert isinstance(result, EvaluationResult)

        # Verify candidate_profile
        assert isinstance(result.candidate_profile, CandidateProfile)
        assert len(result.candidate_profile.skills) == 4
        assert result.candidate_profile.skills[0].name == "Python"
        assert result.candidate_profile.total_years_experience == 4.0

        # Verify job_profile
        assert isinstance(result.job_profile, JobProfile)
        assert result.job_profile.role == "Senior Backend Engineer"
        assert len(result.job_profile.must_have_skills) == 3

        # Verify evaluation
        assert isinstance(result.evaluation, RecruiterEvaluation)
        assert result.evaluation.match_level == "partial_match"
        assert result.evaluation.hiring_confidence == 55
        assert len(result.evaluation.strengths) == 2
        assert len(result.evaluation.gaps) == 2

        # Verify all 3 LLM calls were made
        assert mock_client.generate_json.call_count == 3

    @pytest.mark.asyncio
    async def test_pipeline_to_dict(self) -> None:
        """EvaluationResult.to_dict() serializes all components."""
        pipeline, _ = _build_pipeline([
            RESUME_ANALYZER_LLM_RESPONSE,
            JD_ANALYZER_LLM_RESPONSE,
            RECRUITER_LLM_RESPONSE,
        ])

        result = await pipeline.run(
            raw_resume_text=SAMPLE_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        output = result.to_dict()
        assert "candidate_profile" in output
        assert "job_profile" in output
        assert "evaluation" in output
        assert isinstance(output["candidate_profile"], dict)
        assert isinstance(output["job_profile"], dict)
        assert isinstance(output["evaluation"], dict)
        assert output["evaluation"]["match_level"] == "partial_match"

    @pytest.mark.asyncio
    async def test_pipeline_passes_context_between_agents(self) -> None:
        """Verify recruiter agent receives output of previous agents."""
        pipeline, mock_client = _build_pipeline([
            RESUME_ANALYZER_LLM_RESPONSE,
            JD_ANALYZER_LLM_RESPONSE,
            RECRUITER_LLM_RESPONSE,
        ])

        await pipeline.run(raw_resume_text=SAMPLE_RESUME, raw_jd_text=SAMPLE_JD)

        # Recruiter prompt (3rd call) should contain serialized candidate + job data
        recruiter_prompt = mock_client.generate_json.call_args_list[2][0][0]
        assert "Python" in recruiter_prompt
        assert "Senior Backend Engineer" in recruiter_prompt
        assert "Kubernetes" in recruiter_prompt

    @pytest.mark.asyncio
    async def test_pipeline_reports_meaningful_progress_updates(self) -> None:
        """Pipeline progress callbacks follow the evaluation stages."""
        pipeline, _ = _build_pipeline([
            RESUME_ANALYZER_LLM_RESPONSE,
            JD_ANALYZER_LLM_RESPONSE,
            RECRUITER_LLM_RESPONSE,
        ])
        progress_updates: list[tuple[int, str]] = []

        def record_progress(progress: int, current_step: str) -> None:
            progress_updates.append((progress, current_step))

        await pipeline.run(
            raw_resume_text=SAMPLE_RESUME,
            raw_jd_text=SAMPLE_JD,
            progress_callback=record_progress,
        )

        assert progress_updates == [
            (10, "Initializing"),
            (25, "Resume extraction"),
            (35, "Resume analysis"),
            (45, "Resume analysis complete"),
            (55, "Job description analysis"),
            (60, "Job description analysis complete"),
            (70, "Recruiter review"),
            (80, "Recruiter review complete"),
            (95, "Suggestions generation"),
        ]


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------


class TestEvaluationPipelineInputValidation:
    @pytest.mark.asyncio
    async def test_empty_resume_text_raises(self) -> None:
        pipeline, _ = _build_pipeline([])

        with pytest.raises(PipelineInputError, match="raw_resume_text"):
            await pipeline.run(raw_resume_text="", raw_jd_text=SAMPLE_JD)

    @pytest.mark.asyncio
    async def test_whitespace_resume_text_raises(self) -> None:
        pipeline, _ = _build_pipeline([])

        with pytest.raises(PipelineInputError, match="raw_resume_text"):
            await pipeline.run(raw_resume_text="   \n  ", raw_jd_text=SAMPLE_JD)

    @pytest.mark.asyncio
    async def test_empty_jd_text_raises(self) -> None:
        pipeline, _ = _build_pipeline([])

        with pytest.raises(PipelineInputError, match="raw_jd_text"):
            await pipeline.run(raw_resume_text=SAMPLE_RESUME, raw_jd_text="")

    @pytest.mark.asyncio
    async def test_whitespace_jd_text_raises(self) -> None:
        pipeline, _ = _build_pipeline([])

        with pytest.raises(PipelineInputError, match="raw_jd_text"):
            await pipeline.run(raw_resume_text=SAMPLE_RESUME, raw_jd_text="  \t  ")


# ---------------------------------------------------------------------------
# Error propagation tests
# ---------------------------------------------------------------------------


class TestEvaluationPipelineErrors:
    @pytest.mark.asyncio
    async def test_resume_analyzer_failure_propagates(self) -> None:
        """Pipeline wraps agent errors in PipelineError."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("broken json")

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = EvaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(PipelineError, match="ResumeAnalyzerAgent.*failed"):
            await pipeline.run(raw_resume_text=SAMPLE_RESUME, raw_jd_text=SAMPLE_JD)

    @pytest.mark.asyncio
    async def test_jd_analyzer_failure_propagates(self) -> None:
        """Second agent failure after first succeeds."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            RESUME_ANALYZER_LLM_RESPONSE,
            LLMParseError("bad jd json"),
        ]

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = EvaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(PipelineError, match="JDAnalyzerAgent.*failed"):
            await pipeline.run(raw_resume_text=SAMPLE_RESUME, raw_jd_text=SAMPLE_JD)

    @pytest.mark.asyncio
    async def test_recruiter_failure_propagates(self) -> None:
        """Third agent failure after first two succeed."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            RESUME_ANALYZER_LLM_RESPONSE,
            JD_ANALYZER_LLM_RESPONSE,
            LLMParseError("bad recruiter json"),
        ]

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = EvaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(PipelineError, match="RecruiterAgent.*failed"):
            await pipeline.run(raw_resume_text=SAMPLE_RESUME, raw_jd_text=SAMPLE_JD)

    @pytest.mark.asyncio
    async def test_api_error_wrapped_in_pipeline_error(self) -> None:
        """LLMAPIError is also wrapped in PipelineError."""
        from services.llm import LLMAPIError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMAPIError("quota exceeded")

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = EvaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(PipelineError):
            await pipeline.run(raw_resume_text=SAMPLE_RESUME, raw_jd_text=SAMPLE_JD)


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEvaluationPipelineEdgeCases:
    @pytest.mark.asyncio
    async def test_llm_wraps_response_in_single_key(self) -> None:
        """Agents handle LLM responses wrapped in a top-level key."""
        pipeline, _ = _build_pipeline([
            {"candidate": RESUME_ANALYZER_LLM_RESPONSE},  # wrapped
            {"result": JD_ANALYZER_LLM_RESPONSE},  # wrapped
            {"output": RECRUITER_LLM_RESPONSE},  # wrapped
        ])

        result = await pipeline.run(
            raw_resume_text=SAMPLE_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        assert isinstance(result, EvaluationResult)
        assert result.candidate_profile.skills[0].name == "Python"
        assert result.job_profile.role == "Senior Backend Engineer"
        assert result.evaluation.match_level == "partial_match"

    @pytest.mark.asyncio
    async def test_result_is_frozen_dataclass(self) -> None:
        """EvaluationResult is immutable."""
        pipeline, _ = _build_pipeline([
            RESUME_ANALYZER_LLM_RESPONSE,
            JD_ANALYZER_LLM_RESPONSE,
            RECRUITER_LLM_RESPONSE,
        ])

        result = await pipeline.run(
            raw_resume_text=SAMPLE_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        with pytest.raises(AttributeError):
            result.candidate_profile = None  # type: ignore[misc]
