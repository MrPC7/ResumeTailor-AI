"""In-memory job management for future asynchronous workflows."""
from __future__ import annotations

from threading import RLock
from typing import Any
from uuid import uuid4

from schemas.job import Job, JobStatus, utc_now


class JobNotFoundError(KeyError):
    """Raised when a job id does not exist in the manager."""


class JobManager:
    """Thread-safe in-memory store for job state.

    This service is intentionally process-local infrastructure. It can be
    swapped for a durable backend when asynchronous execution is introduced.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = RLock()

    def create_job(self) -> Job:
        """Create and store a new pending job."""
        job = Job(job_id=str(uuid4()))
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Job:
        """Return an existing job by id."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)
            return job

    def update_progress(
        self,
        job_id: str,
        progress: int,
        current_step: str | None = None,
    ) -> Job:
        """Update progress and mark the job as running."""
        updates: dict[str, Any] = {
            "status": JobStatus.IN_PROGRESS,
            "progress": progress,
            "updated_at": utc_now(),
            "error_message": None,
        }
        if current_step is not None:
            updates["current_step"] = current_step
        return self._update_job(job_id, **updates)

    def complete_job(self, job_id: str, result: Any) -> Job:
        """Mark a job as completed and attach its result."""
        return self._update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            updated_at=utc_now(),
            error_message=None,
            result=result,
        )

    def fail_job(self, job_id: str, error: str) -> Job:
        """Mark a job as failed with an error message."""
        return self._update_job(
            job_id,
            status=JobStatus.FAILED,
            updated_at=utc_now(),
            error_message=error,
        )

    def _update_job(self, job_id: str, **updates: Any) -> Job:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)

            data = job.model_dump()
            data.update(updates)
            updated_job = Job.model_validate(data)
            self._jobs[job_id] = updated_job
            return updated_job


job_manager = JobManager()
