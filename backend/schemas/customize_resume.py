from pydantic import BaseModel, ConfigDict, Field

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import (
    EducationItem,
    ExperienceItem,
    ExtractResumeResponse,
    ProjectItem,
)


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


class CustomizeSuggestion(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    description: str
    priority: str = ""
    estimated_impact: str = ""
    affected_section: str = ""


class CustomizeResumeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resume: ExtractResumeResponse
    jd: AnalyzeJDResponse
    selected_suggestion_ids: list[str] = Field(default_factory=list, alias="selectedSuggestionIds")
    suggestions: list[CustomizeSuggestion] = Field(default_factory=list)


class CustomizeResumeResponse(BaseModel):
    customizedResume: ExtractResumeResponse
    suggestions: list[str]
    compressed: bool = False
