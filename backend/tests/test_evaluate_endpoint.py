"""Tests for POST /api/evaluate endpoint."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from schemas.agent_models import (
    CandidateProfile,
    ExperienceRequirement,
    JobProfile,
    RecruiterEvaluation,
    RequiredSkill,
    Responsibility,
    Skill,
    WorkExperience,
)
from schemas.job import JobStatus
from services.orchestrator.evaluation_pipeline import EvaluationResult, PipelineError


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


class TestEvaluateEndpointSuccess:
    @patch("api.evaluate._pipeline")
    def test_returns_job_id_and_starts_background_evaluation(
        self,
        mock_pipeline: AsyncMock,
        client: TestClient,
    ) -> None:
        from api.evaluate import job_manager

        async def run_pipeline(**kwargs: object) -> EvaluationResult:
            progress_callback = kwargs["progress_callback"]
            await progress_callback(25, "Resume extraction")
            await progress_callback(45, "Resume analysis complete")
            await progress_callback(60, "Job description analysis complete")
            await progress_callback(80, "Recruiter review complete")
            await progress_callback(95, "Suggestions generation")
            return SAMPLE_RESULT

        mock_pipeline.run = AsyncMock(side_effect=run_pipeline)

        response = client.post("/api/evaluate", json=VALID_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert list(data.keys()) == ["job_id"]
        assert data["job_id"]

        job = job_manager.get_job(data["job_id"])
        assert job.status == JobStatus.COMPLETED
        assert job.progress == 100
        assert job.current_step == "Completed"
        assert job.error is None
        assert job.result["candidateProfile"]["skills"][0]["name"] == "Python"
        assert job.result["suggestions"] == []

        call_kwargs = mock_pipeline.run.await_args.kwargs
        assert call_kwargs["raw_resume_text"] == VALID_REQUEST["rawResumeText"]
        assert call_kwargs["raw_jd_text"] == VALID_REQUEST["rawJdText"]
        assert callable(call_kwargs["progress_callback"])

    @patch("api.evaluate._pipeline")
    def test_get_evaluation_job_returns_tracked_lifecycle(
        self,
        mock_pipeline: AsyncMock,
        client: TestClient,
    ) -> None:
        mock_pipeline.run = AsyncMock(return_value=SAMPLE_RESULT)

        create_response = client.post("/api/evaluate", json=VALID_REQUEST)
        job_id = create_response.json()["job_id"]

        response = client.get(f"/api/evaluate/{job_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "COMPLETED"
        assert data["progress"] == 100
        assert data["current_step"] == "Completed"
        assert data["error"] is None
        assert data["result"]["suggestions"] == []


class TestEvaluateEndpointValidation:
    def test_missing_resume_text_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/evaluate", json={"rawJdText": "Some JD"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_jd_text_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/evaluate", json={"rawResumeText": "Some resume"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_resume_text_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/evaluate",
            json={
                "rawResumeText": "",
                "rawJdText": "Some JD",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_jd_text_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/evaluate",
            json={
                "rawResumeText": "Some resume",
                "rawJdText": "",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/evaluate", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestEvaluateEndpointErrors:
    @patch("api.evaluate._pipeline")
    def test_pipeline_error_fails_background_job(
        self,
        mock_pipeline: AsyncMock,
        client: TestClient,
    ) -> None:
        from api.evaluate import job_manager

        mock_pipeline.run = AsyncMock(
            side_effect=PipelineError("Agent failed: invalid json response")
        )

        response = client.post("/api/evaluate", json=VALID_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        job = job_manager.get_job(response.json()["job_id"])
        assert job.status == JobStatus.FAILED
        assert job.current_step == "Failed"
        assert job.error == "Agent failed: invalid json response"
        assert job.progress < 100

    def test_get_evaluation_job_returns_404_for_missing_job(
        self,
        client: TestClient,
    ) -> None:
        response = client.get("/api/evaluate/missing")

        assert response.status_code == status.HTTP_404_NOT_FOUND
