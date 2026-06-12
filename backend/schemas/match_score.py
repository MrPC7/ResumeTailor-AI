from pydantic import BaseModel, ConfigDict, Field

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse


class MatchScoreRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resume: ExtractResumeResponse
    jd: AnalyzeJDResponse


class MatchScoreResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    skillScore: int = Field(ge=0, le=100)
    keywordScore: int = Field(ge=0, le=100)
    experienceScore: int = Field(ge=0, le=100)
