"""Tests for in-memory job management infrastructure."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.job import Job, JobStatus
from services.job_manager import JobManager, JobNotFoundError


def test_create_job_initializes_pending_job() -> None:
    manager = JobManager()

    job = manager.create_job()

    assert job.job_id
    assert job.status == JobStatus.PENDING
    assert job.progress == 0
    assert job.current_step is None
    assert job.error_message is None
    assert job.result is None
    assert job.created_at <= job.updated_at


def test_get_job_returns_existing_job() -> None:
    manager = JobManager()
    job = manager.create_job()

    assert manager.get_job(job.job_id) == job


def test_get_job_raises_for_missing_job() -> None:
    manager = JobManager()

    with pytest.raises(JobNotFoundError):
        manager.get_job("missing")


def test_update_progress_marks_job_in_progress() -> None:
    manager = JobManager()
    job = manager.create_job()

    updated = manager.update_progress(job.job_id, progress=25, current_step="Parsing")

    assert updated.status == JobStatus.IN_PROGRESS
    assert updated.progress == 25
    assert updated.current_step == "Parsing"
    assert updated.error_message is None
    assert updated.updated_at >= job.updated_at


def test_complete_job_sets_result_and_full_progress() -> None:
    manager = JobManager()
    job = manager.create_job()

    completed = manager.complete_job(job.job_id, result={"score": 92})

    assert completed.status == JobStatus.COMPLETED
    assert completed.progress == 100
    assert completed.result == {"score": 92}
    assert completed.error_message is None


def test_fail_job_sets_error_message() -> None:
    manager = JobManager()
    job = manager.create_job()

    failed = manager.fail_job(job.job_id, error="Provider unavailable")

    assert failed.status == JobStatus.FAILED
    assert failed.error_message == "Provider unavailable"


def test_job_progress_is_bounded() -> None:
    with pytest.raises(ValidationError):
        Job(job_id="job-1", progress=101)


def test_update_progress_validates_bounds() -> None:
    manager = JobManager()
    job = manager.create_job()

    with pytest.raises(ValidationError):
        manager.update_progress(job.job_id, progress=101)
