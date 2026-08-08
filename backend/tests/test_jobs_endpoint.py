"""Tests for GET /jobs/{job_id} endpoint."""
from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from main import app

    return TestClient(app)


def test_get_existing_job_returns_current_state(client: TestClient) -> None:
    from api.jobs import job_manager

    job = job_manager.create_job()
    job_manager.update_progress(job.job_id, 45, "Resume analysis")
    before = job_manager.get_job(job.job_id)

    response = client.get(f"/jobs/{job.job_id}")
    after = job_manager.get_job(job.job_id)

    assert response.status_code == status.HTTP_200_OK
    assert after == before
    data = response.json()
    assert data == {
        "job_id": job.job_id,
        "status": "PROCESSING",
        "progress": 45,
        "current_step": "Resume analysis",
        "error": None,
        "result": None,
    }


def test_get_completed_job_includes_result(client: TestClient) -> None:
    from api.jobs import job_manager

    job = job_manager.create_job()
    job_manager.complete_job(job.job_id, {"suggestions": [{"title": "Add metrics"}]})

    response = client.get(f"/jobs/{job.job_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["job_id"] == job.job_id
    assert data["status"] == "COMPLETED"
    assert data["progress"] == 100
    assert data["current_step"] == "Completed"
    assert data["error"] is None
    assert data["result"] == {"suggestions": [{"title": "Add metrics"}]}


def test_get_failed_job_returns_failure_state_without_result(
    client: TestClient,
) -> None:
    from api.jobs import job_manager

    job = job_manager.create_job()
    job_manager.update_progress(job.job_id, 60, "Job description analysis complete")
    job_manager.fail_job(job.job_id, "LLM provider timed out")

    response = client.get(f"/jobs/{job.job_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["job_id"] == job.job_id
    assert data["status"] == "FAILED"
    assert data["progress"] == 60
    assert data["current_step"] == "Failed"
    assert data["error"] == "LLM provider timed out"
    assert data["result"] is None


def test_get_unknown_job_returns_404(client: TestClient) -> None:
    response = client.get("/jobs/unknown-job-id")

    assert response.status_code == status.HTTP_404_NOT_FOUND
