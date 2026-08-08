"""Read-only job status endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from schemas.job import Job, JobStatus, JobStatusResponse
from services.job_manager import JobNotFoundError, job_manager

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    try:
        job = job_manager.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        ) from exc

    return _build_job_status_response(job)


def _build_job_status_response(job: Job) -> JobStatusResponse:
    result = job.result if job.status == JobStatus.COMPLETED else None
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        current_step=job.current_step,
        error=job.error,
        result=result,
    )
