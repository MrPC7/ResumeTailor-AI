"""Request/response schemas for the re-evaluation endpoint."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from schemas.agent_models import ImprovementMetrics, RecruiterEvaluation


class ReevaluateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    original_resume_text: str = Field(
        alias="originalResumeText",
        min_length=1,
        max_length=100_000,
    )
    optimized_resume_text: str = Field(
        alias="optimizedResumeText",
        min_length=1,
        max_length=100_000,
    )
    raw_jd_text: str = Field(
        alias="rawJdText",
        min_length=1,
        max_length=50_000,
    )


class ReevaluateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, by_alias=True)

    before: RecruiterEvaluation
    after: RecruiterEvaluation
    improvement: ImprovementMetrics
