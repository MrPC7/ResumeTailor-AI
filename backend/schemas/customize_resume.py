from pydantic import BaseModel, ConfigDict, Field

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import (
    EducationItem,
    ExperienceItem,
    ExtractResumeResponse,
    ProjectItem,
)
from schemas.gap_analysis import GapAnalysisResponse


# Internal model that mirrors ExtractResumeResponse with extra="ignore"
# so unexpected keys from Gemini don't fail validation.
class CustomizedResumeData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    summary: str | None = None
    skills: list[str] = []
    experience: list[ExperienceItem] = []
    education: list[EducationItem] = []
    projects: list[ProjectItem] = []


# Internal wrapper used to validate full LLM JSON response.
class CustomizeResumeRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    customizedResume: CustomizedResumeData
    suggestions: list[str] = []


class CustomizeResumeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resume: ExtractResumeResponse
    jd: AnalyzeJDResponse
    gap_analysis: GapAnalysisResponse | None = Field(default=None, alias="gapAnalysis")


class CustomizeResumeResponse(BaseModel):
    customizedResume: ExtractResumeResponse
    suggestions: list[str]
