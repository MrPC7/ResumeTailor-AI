"""Schemas for backend job execution infrastructure."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    """Lifecycle states for in-memory jobs."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Job(BaseModel):
    """Represents asynchronous work tracked by the backend."""

    job_id: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str | None = None
    error_message: str | None = None
    result: Any | None = None

    model_config = ConfigDict(use_enum_values=True)
