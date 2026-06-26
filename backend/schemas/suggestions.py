"""Request/response schemas for the v2 suggestions endpoint."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    SuggestionReport,
)


class SuggestionsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    candidate_profile: CandidateProfile = Field(alias="candidateProfile")
    job_profile: JobProfile = Field(alias="jobProfile")
    evaluation: RecruiterEvaluation


class SuggestionsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, by_alias=True)

    suggestions: SuggestionReport
