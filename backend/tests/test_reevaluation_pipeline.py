"""Integration tests for ReevaluationPipeline — tests the full re-evaluation flow."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.agent_models import (
    CandidateProfile,
    ImprovementMetrics,
    JobProfile,
    RecruiterEvaluation,
)
from services.orchestrator.reevaluation_pipeline import (
    ReevaluationPipeline,
    ReevaluationPipelineError,
    ReevaluationInputError,
    ReevaluationResult,
)


# ---------------------------------------------------------------------------
# LLM response fixtures
# ---------------------------------------------------------------------------

ORIGINAL_RESUME_ANALYZER_RESPONSE: dict[str, Any] = {
    "skills": [
        {"name": "Python", "category": "Programming Language"},
        {"name": "FastAPI", "category": "Framework"},
        {"name": "Docker", "category": "DevOps"},
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

OPTIMIZED_RESUME_ANALYZER_RESPONSE: dict[str, Any] = {
    "skills": [
        {"name": "Python", "category": "Programming Language"},
        {"name": "FastAPI", "category": "Framework"},
        {"name": "Docker", "category": "DevOps"},
        {"name": "Kubernetes", "category": "DevOps"},
        {"name": "PostgreSQL", "category": "Database"},
    ],
    "work_experience": [
        {
            "company": "Acme Corp",
            "position": "Senior Backend Engineer",
            "duration": "2021 - Present",
            "responsibilities": [
                "Designed and built scalable REST APIs with FastAPI",
                "Led Docker and Kubernetes deployments for microservices",
                "Mentored junior engineers on API design patterns",
            ],
            "technologies": ["Python", "FastAPI", "Docker", "Kubernetes"],
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
            "description": "Production REST task manager serving 10k requests/day",
            "technologies": ["FastAPI", "PostgreSQL", "Docker"],
            "role": "Lead developer",
        }
    ],
    "certifications": [],
    "total_years_experience": 4.0,
    "primary_domain": "Backend Development",
}

JD_ANALYZER_RESPONSE: dict[str, Any] = {
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

BEFORE_RECRUITER_RESPONSE: dict[str, Any] = {
    "match_level": "partial_match",
    "hiring_confidence": 45,
    "interview_probability": 40,
    "strengths": [
        "Strong Python + FastAPI proficiency",
    ],
    "gaps": [
        "No Kubernetes experience — must-have",
        "4 years experience vs 5 years required",
        "No mentoring evidence",
    ],
    "verdict": "Partial fit — missing Kubernetes and mentoring experience.",
    "reasoning": [
        "2 of 3 must-have skills present",
        "Missing Kubernetes is critical",
        "No leadership evidence",
    ],
}

AFTER_RECRUITER_RESPONSE: dict[str, Any] = {
    "match_level": "good_match",
    "hiring_confidence": 75,
    "interview_probability": 80,
    "strengths": [
        "Strong Python + FastAPI proficiency",
        "Kubernetes deployment experience demonstrated",
        "Mentoring junior engineers",
        "Production-scale project evidence",
    ],
    "gaps": [
        "4 years experience vs 5 years required",
    ],
    "verdict": "Good fit — all must-have skills present, slight experience gap.",
    "reasoning": [
        "3 of 3 must-have skills present",
        "Kubernetes gap addressed",
        "Mentoring evidence added",
        "Slight experience shortfall remains",
    ],
}

SAMPLE_ORIGINAL_RESUME = """\
John Doe — Backend Engineer
john@email.com | +1-555-0123

Experience:
Acme Corp — Backend Engineer (2021 - Present)
- Built REST APIs with FastAPI
- Led Docker-based deployments

Education:
MIT — B.S. Computer Science (2020)

Skills: Python, FastAPI, Docker

Projects:
TaskAPI — REST task manager built with FastAPI and PostgreSQL
"""

SAMPLE_OPTIMIZED_RESUME = """\
John Doe — Senior Backend Engineer
john@email.com | +1-555-0123

Experience:
Acme Corp — Senior Backend Engineer (2021 - Present)
- Designed and built scalable REST APIs with FastAPI
- Led Docker and Kubernetes deployments for microservices
- Mentored junior engineers on API design patterns

Education:
MIT — B.S. Computer Science (2020)

Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL

Projects:
TaskAPI — Production REST task manager serving 10k requests/day
Built with FastAPI, PostgreSQL, Docker
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
) -> tuple[ReevaluationPipeline, AsyncMock]:
    """Create pipeline with a mock LLM client that returns responses in order."""
    mock_client = AsyncMock()
    mock_client.generate_json.side_effect = llm_responses

    from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
    from services.agents.jd_analyzer.agent import JDAnalyzerAgent
    from services.agents.recruiter.agent import RecruiterAgent

    pipeline = ReevaluationPipeline(
        resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
        jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
        recruiter=RecruiterAgent(client=mock_client, max_retries=1),
    )
    return pipeline, mock_client


# ---------------------------------------------------------------------------
# Integration tests — full pipeline
# ---------------------------------------------------------------------------


class TestReevaluationPipelineIntegration:
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self) -> None:
        """Full pipeline produces before/after evaluations and improvement metrics."""
        pipeline, mock_client = _build_pipeline([
            ORIGINAL_RESUME_ANALYZER_RESPONSE,   # Step 1: analyze original
            JD_ANALYZER_RESPONSE,                 # Step 2: analyze JD
            BEFORE_RECRUITER_RESPONSE,            # Step 3: evaluate original
            OPTIMIZED_RESUME_ANALYZER_RESPONSE,   # Step 4: analyze optimized
            AFTER_RECRUITER_RESPONSE,             # Step 5: evaluate optimized
        ])

        result = await pipeline.run(
            original_resume_text=SAMPLE_ORIGINAL_RESUME,
            optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        assert isinstance(result, ReevaluationResult)

        # Before evaluation
        assert isinstance(result.before, RecruiterEvaluation)
        assert result.before.match_level == "partial_match"
        assert result.before.hiring_confidence == 45
        assert result.before.interview_probability == 40
        assert len(result.before.gaps) == 3

        # After evaluation
        assert isinstance(result.after, RecruiterEvaluation)
        assert result.after.match_level == "good_match"
        assert result.after.hiring_confidence == 75
        assert result.after.interview_probability == 80
        assert len(result.after.gaps) == 1

        # Improvement metrics
        assert isinstance(result.improvement, ImprovementMetrics)
        assert result.improvement.hiring_confidence_delta == 30
        assert result.improvement.interview_probability_delta == 40
        assert result.improvement.gaps_before == 3
        assert result.improvement.gaps_after == 1
        assert result.improvement.gaps_reduced == 2
        assert result.improvement.strengths_before == 1
        assert result.improvement.strengths_after == 4
        assert result.improvement.strengths_gained == 3
        assert result.improvement.match_level_before == "partial_match"
        assert result.improvement.match_level_after == "good_match"
        assert result.improvement.improved is True

        # All 5 LLM calls were made
        assert mock_client.generate_json.call_count == 5

    @pytest.mark.asyncio
    async def test_pipeline_to_dict(self) -> None:
        """ReevaluationResult.to_dict() serializes all components."""
        pipeline, _ = _build_pipeline([
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            JD_ANALYZER_RESPONSE,
            BEFORE_RECRUITER_RESPONSE,
            OPTIMIZED_RESUME_ANALYZER_RESPONSE,
            AFTER_RECRUITER_RESPONSE,
        ])

        result = await pipeline.run(
            original_resume_text=SAMPLE_ORIGINAL_RESUME,
            optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        output = result.to_dict()
        assert "before" in output
        assert "after" in output
        assert "improvement" in output
        assert isinstance(output["before"], dict)
        assert isinstance(output["after"], dict)
        assert isinstance(output["improvement"], dict)
        assert output["before"]["match_level"] == "partial_match"
        assert output["after"]["match_level"] == "good_match"
        assert output["improvement"]["hiring_confidence_delta"] == 30

    @pytest.mark.asyncio
    async def test_no_improvement_scenario(self) -> None:
        """Pipeline handles case where optimized resume scores same or lower."""
        same_after = {
            **BEFORE_RECRUITER_RESPONSE,
            "hiring_confidence": 40,
            "interview_probability": 35,
        }

        pipeline, _ = _build_pipeline([
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            JD_ANALYZER_RESPONSE,
            BEFORE_RECRUITER_RESPONSE,
            OPTIMIZED_RESUME_ANALYZER_RESPONSE,
            same_after,
        ])

        result = await pipeline.run(
            original_resume_text=SAMPLE_ORIGINAL_RESUME,
            optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        assert result.improvement.improved is False
        assert result.improvement.hiring_confidence_delta == -5
        assert result.improvement.interview_probability_delta == -5

    @pytest.mark.asyncio
    async def test_result_is_frozen_dataclass(self) -> None:
        """ReevaluationResult is immutable."""
        pipeline, _ = _build_pipeline([
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            JD_ANALYZER_RESPONSE,
            BEFORE_RECRUITER_RESPONSE,
            OPTIMIZED_RESUME_ANALYZER_RESPONSE,
            AFTER_RECRUITER_RESPONSE,
        ])

        result = await pipeline.run(
            original_resume_text=SAMPLE_ORIGINAL_RESUME,
            optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        with pytest.raises(AttributeError):
            result.before = None  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------


class TestReevaluationPipelineInputValidation:
    @pytest.mark.asyncio
    async def test_empty_original_resume_raises(self) -> None:
        pipeline, _ = _build_pipeline([])
        with pytest.raises(ReevaluationInputError, match="original_resume_text"):
            await pipeline.run(
                original_resume_text="",
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_whitespace_original_resume_raises(self) -> None:
        pipeline, _ = _build_pipeline([])
        with pytest.raises(ReevaluationInputError, match="original_resume_text"):
            await pipeline.run(
                original_resume_text="   \n  ",
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_empty_optimized_resume_raises(self) -> None:
        pipeline, _ = _build_pipeline([])
        with pytest.raises(ReevaluationInputError, match="optimized_resume_text"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text="",
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_whitespace_optimized_resume_raises(self) -> None:
        pipeline, _ = _build_pipeline([])
        with pytest.raises(ReevaluationInputError, match="optimized_resume_text"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text="  \t  ",
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_empty_jd_text_raises(self) -> None:
        pipeline, _ = _build_pipeline([])
        with pytest.raises(ReevaluationInputError, match="raw_jd_text"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text="",
            )

    @pytest.mark.asyncio
    async def test_whitespace_jd_text_raises(self) -> None:
        pipeline, _ = _build_pipeline([])
        with pytest.raises(ReevaluationInputError, match="raw_jd_text"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text="  \t  ",
            )


# ---------------------------------------------------------------------------
# Error propagation tests
# ---------------------------------------------------------------------------


class TestReevaluationPipelineErrors:
    @pytest.mark.asyncio
    async def test_original_resume_analyzer_failure_propagates(self) -> None:
        """Step 1 failure wraps in ReevaluationPipelineError."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMParseError("broken json")

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = ReevaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(ReevaluationPipelineError, match="ResumeAnalyzerAgent.*failed"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_jd_analyzer_failure_propagates(self) -> None:
        """Step 2 failure after step 1 succeeds."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            LLMParseError("bad jd json"),
        ]

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = ReevaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(ReevaluationPipelineError, match="JDAnalyzerAgent.*failed"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_before_recruiter_failure_propagates(self) -> None:
        """Step 3 (before eval) failure."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            JD_ANALYZER_RESPONSE,
            LLMParseError("bad recruiter json"),
        ]

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = ReevaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(ReevaluationPipelineError, match="RecruiterAgent.*failed"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_optimized_resume_analyzer_failure_propagates(self) -> None:
        """Step 4 (optimized analysis) failure."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            JD_ANALYZER_RESPONSE,
            BEFORE_RECRUITER_RESPONSE,
            LLMParseError("bad optimized json"),
        ]

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = ReevaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(ReevaluationPipelineError, match="ResumeAnalyzerAgent.*failed"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_after_recruiter_failure_propagates(self) -> None:
        """Step 5 (after eval) failure."""
        from services.llm import LLMParseError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = [
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            JD_ANALYZER_RESPONSE,
            BEFORE_RECRUITER_RESPONSE,
            OPTIMIZED_RESUME_ANALYZER_RESPONSE,
            LLMParseError("bad after recruiter json"),
        ]

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = ReevaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(ReevaluationPipelineError, match="RecruiterAgent.*failed"):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text=SAMPLE_JD,
            )

    @pytest.mark.asyncio
    async def test_api_error_wrapped_in_pipeline_error(self) -> None:
        """LLMAPIError is wrapped in ReevaluationPipelineError."""
        from services.llm import LLMAPIError

        mock_client = AsyncMock()
        mock_client.generate_json.side_effect = LLMAPIError("quota exceeded")

        from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
        from services.agents.jd_analyzer.agent import JDAnalyzerAgent
        from services.agents.recruiter.agent import RecruiterAgent

        pipeline = ReevaluationPipeline(
            resume_analyzer=ResumeAnalyzerAgent(client=mock_client, max_retries=1),
            jd_analyzer=JDAnalyzerAgent(client=mock_client, max_retries=1),
            recruiter=RecruiterAgent(client=mock_client, max_retries=1),
        )

        with pytest.raises(ReevaluationPipelineError):
            await pipeline.run(
                original_resume_text=SAMPLE_ORIGINAL_RESUME,
                optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
                raw_jd_text=SAMPLE_JD,
            )


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestReevaluationPipelineEdgeCases:
    @pytest.mark.asyncio
    async def test_llm_wraps_responses_in_single_key(self) -> None:
        """Agents handle LLM responses wrapped in a top-level key."""
        pipeline, _ = _build_pipeline([
            {"candidate": ORIGINAL_RESUME_ANALYZER_RESPONSE},
            {"result": JD_ANALYZER_RESPONSE},
            {"output": BEFORE_RECRUITER_RESPONSE},
            {"candidate": OPTIMIZED_RESUME_ANALYZER_RESPONSE},
            {"output": AFTER_RECRUITER_RESPONSE},
        ])

        result = await pipeline.run(
            original_resume_text=SAMPLE_ORIGINAL_RESUME,
            optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        assert isinstance(result, ReevaluationResult)
        assert result.before.match_level == "partial_match"
        assert result.after.match_level == "good_match"
        assert result.improvement.improved is True

    @pytest.mark.asyncio
    async def test_recruiter_called_twice(self) -> None:
        """Verify recruiter agent is called exactly twice (before + after)."""
        pipeline, mock_client = _build_pipeline([
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            JD_ANALYZER_RESPONSE,
            BEFORE_RECRUITER_RESPONSE,
            OPTIMIZED_RESUME_ANALYZER_RESPONSE,
            AFTER_RECRUITER_RESPONSE,
        ])

        await pipeline.run(
            original_resume_text=SAMPLE_ORIGINAL_RESUME,
            optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        # 5 total calls: 2 resume analyzer + 1 JD analyzer + 2 recruiter
        assert mock_client.generate_json.call_count == 5

    @pytest.mark.asyncio
    async def test_improvement_metrics_deterministic(self) -> None:
        """Improvement metrics are computed deterministically from before/after."""
        pipeline, _ = _build_pipeline([
            ORIGINAL_RESUME_ANALYZER_RESPONSE,
            JD_ANALYZER_RESPONSE,
            BEFORE_RECRUITER_RESPONSE,
            OPTIMIZED_RESUME_ANALYZER_RESPONSE,
            AFTER_RECRUITER_RESPONSE,
        ])

        result = await pipeline.run(
            original_resume_text=SAMPLE_ORIGINAL_RESUME,
            optimized_resume_text=SAMPLE_OPTIMIZED_RESUME,
            raw_jd_text=SAMPLE_JD,
        )

        # Verify metrics are computed from before/after, not from LLM
        imp = result.improvement
        assert imp.hiring_confidence_delta == (
            result.after.hiring_confidence - result.before.hiring_confidence
        )
        assert imp.interview_probability_delta == (
            result.after.interview_probability - result.before.interview_probability
        )
        assert imp.gaps_reduced == len(result.before.gaps) - len(result.after.gaps)
        assert imp.strengths_gained == len(result.after.strengths) - len(result.before.strengths)
