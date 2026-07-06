"""Request/response schemas for the v2 evaluation endpoint."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from schemas.agent_models import CandidateProfile, JobProfile, RecruiterEvaluation, Suggestion


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    raw_resume_text: str = Field(
        alias="rawResumeText",
        min_length=1,
        max_length=100_000,
    )
    raw_jd_text: str = Field(
        alias="rawJdText",
        min_length=1,
        max_length=50_000,
    )


class EvaluateResponse(BaseModel):
    candidate_profile: CandidateProfile = Field(alias="candidateProfile")
    job_profile: JobProfile = Field(alias="jobProfile")
    evaluation: RecruiterEvaluation
    suggestions: list[Suggestion] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, by_alias=True)
