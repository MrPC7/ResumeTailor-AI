"""Schemas for backend job execution infrastructure."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    """Lifecycle states for in-memory jobs."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Job(BaseModel):
    """Represents asynchronous work tracked by the backend."""

    job_id: str
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str | None = None
    error: str | None = None
    result: Any | None = None

    model_config = ConfigDict(use_enum_values=True)


class JobStatusResponse(BaseModel):
    """Public API response for job status polling."""

    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    current_step: str | None = None
    error: str | None = None
    result: Any | None = None

    model_config = ConfigDict(use_enum_values=True)
