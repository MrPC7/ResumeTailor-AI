"""Tests for POST /api/evaluate endpoint."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    Skill,
    WorkExperience,
    RequiredSkill,
    Responsibility,
    ExperienceRequirement,
)
from services.orchestrator.evaluation_pipeline import (
    EvaluationResult,
    PipelineError,
    PipelineInputError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CANDIDATE = CandidateProfile(
    skills=[Skill(name="Python", category="Programming Language")],
    work_experience=[
        WorkExperience(
            company="Acme",
            position="Engineer",
            duration="2021 - Present",
            responsibilities=["Built APIs"],
            technologies=["Python"],
        )
    ],
    total_years_experience=4.0,
    primary_domain="Backend",
)

SAMPLE_JOB = JobProfile(
    role="Backend Engineer",
    seniority="Senior",
    must_have_skills=[RequiredSkill(name="Python", category="Programming Language")],
    responsibilities=[Responsibility(description="Build APIs", priority="high")],
    experience_required=ExperienceRequirement(min_years=3.0, domain="Backend"),
)

SAMPLE_EVALUATION = RecruiterEvaluation(
    match_level="good_match",
    hiring_confidence=70,
    interview_probability=75,
    strengths=["Strong Python skills"],
    gaps=["No cloud experience"],
    verdict="Good fit, recommend phone screen.",
    reasoning=["Python matches", "Experience adequate", "Missing cloud is minor"],
)

SAMPLE_RESULT = EvaluationResult(
    candidate_profile=SAMPLE_CANDIDATE,
    job_profile=SAMPLE_JOB,
    evaluation=SAMPLE_EVALUATION,
)

VALID_REQUEST = {
    "rawResumeText": "John Doe\nPython Developer\nExperience: Acme Corp 2021-Present",
    "rawJdText": "Senior Backend Engineer\nRequirements: Python, 3+ years",
}


@pytest.fixture
def client() -> TestClient:
    from main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Success tests
# ---------------------------------------------------------------------------


class TestEvaluateEndpointSuccess:
    @patch("api.evaluate._pipeline")
    def test_returns_200_with_full_result(
        self, mock_pipeline: AsyncMock, client: TestClient
    ) -> None:
        mock_pipeline.run = AsyncMock(return_value=SAMPLE_RESULT)

        response = client.post("/api/evaluate", json=VALID_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "candidateProfile" in data
        assert "jobProfile" in data
        assert "evaluation" in data

    @patch("api.evaluate._pipeline")
    def test_response_contains_candidate_profile(
        self, mock_pipeline: AsyncMock, client: TestClient
    ) -> None:
        mock_pipeline.run = AsyncMock(return_value=SAMPLE_RESULT)

        response = client.post("/api/evaluate", json=VALID_REQUEST)
        data = response.json()

        profile = data["candidateProfile"]
        assert profile["skills"][0]["name"] == "Python"
        assert profile["total_years_experience"] == 4.0

    @patch("api.evaluate._pipeline")
    def test_response_contains_job_profile(
        self, mock_pipeline: AsyncMock, client: TestClient
    ) -> None:
        mock_pipeline.run = AsyncMock(return_value=SAMPLE_RESULT)

        response = client.post("/api/evaluate", json=VALID_REQUEST)
        data = response.json()

        job = data["jobProfile"]
        assert job["role"] == "Backend Engineer"
        assert job["seniority"] == "Senior"

    @patch("api.evaluate._pipeline")
    def test_response_contains_evaluation(
        self, mock_pipeline: AsyncMock, client: TestClient
    ) -> None:
        mock_pipeline.run = AsyncMock(return_value=SAMPLE_RESULT)

        response = client.post("/api/evaluate", json=VALID_REQUEST)
        data = response.json()

        evaluation = data["evaluation"]
        assert evaluation["match_level"] == "good_match"
        assert evaluation["hiring_confidence"] == 70
        assert len(evaluation["strengths"]) == 1
        assert len(evaluation["gaps"]) == 1


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestEvaluateEndpointValidation:
    def test_missing_resume_text_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/evaluate", json={"rawJdText": "Some JD"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_jd_text_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/evaluate", json={"rawResumeText": "Some resume"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_resume_text_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/evaluate", json={
            "rawResumeText": "",
            "rawJdText": "Some JD",
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_jd_text_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/evaluate", json={
            "rawResumeText": "Some resume",
            "rawJdText": "",
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/evaluate", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestEvaluateEndpointErrors:
    @patch("api.evaluate._pipeline")
    def test_pipeline_input_error_returns_422(
        self, mock_pipeline: AsyncMock, client: TestClient
    ) -> None:
        mock_pipeline.run = AsyncMock(
            side_effect=PipelineInputError("raw_resume_text must be non-empty")
        )

        response = client.post("/api/evaluate", json=VALID_REQUEST)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("api.evaluate._pipeline")
    def test_pipeline_error_api_returns_503(
        self, mock_pipeline: AsyncMock, client: TestClient
    ) -> None:
        mock_pipeline.run = AsyncMock(
            side_effect=PipelineError("Agent failed: LLM API error during evaluation")
        )

        response = client.post("/api/evaluate", json=VALID_REQUEST)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @patch("api.evaluate._pipeline")
    def test_pipeline_error_parse_returns_502(
        self, mock_pipeline: AsyncMock, client: TestClient
    ) -> None:
        mock_pipeline.run = AsyncMock(
            side_effect=PipelineError("Agent failed: invalid json response")
        )

        response = client.post("/api/evaluate", json=VALID_REQUEST)
        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    @patch("api.evaluate._pipeline")
    def test_unexpected_error_returns_500(
        self, mock_pipeline: AsyncMock, client: TestClient
    ) -> None:
        mock_pipeline.run = AsyncMock(
            side_effect=RuntimeError("something unexpected")
        )

        response = client.post("/api/evaluate", json=VALID_REQUEST)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR



