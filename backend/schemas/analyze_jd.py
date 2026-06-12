from pydantic import BaseModel, ConfigDict, Field


# Internal model used to validate the raw JSON returned by Gemini.
# extra="ignore" absorbs any unexpected keys the model may emit.
class AnalyzedJD(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str | None = None
    seniority: str | None = None
    required_skills: list[str] = Field(default_factory=list, alias="requiredSkills")
    preferred_skills: list[str] = Field(default_factory=list, alias="preferredSkills")
    ats_keywords: list[str] = Field(default_factory=list, alias="atsKeywords")
    responsibilities: list[str] = Field(default_factory=list)


class AnalyzeJDRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    job_description: str = Field(
        alias="jobDescription",
        min_length=1,
        max_length=20_000,
    )


class AnalyzeJDResponse(BaseModel):
    role: str | None
    seniority: str | None
    requiredSkills: list[str]
    preferredSkills: list[str]
    atsKeywords: list[str]
    responsibilities: list[str]
