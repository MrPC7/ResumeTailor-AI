from pydantic import BaseModel, ConfigDict, Field


class ExperienceItem(BaseModel):
    company: str
    position: str
    duration: str
    description: str


class EducationItem(BaseModel):
    institution: str
    degree: str
    year: str


class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: list[str]


# Internal model used to validate the raw JSON returned by Gemini.
# extra="ignore" absorbs any unexpected keys the model may emit.
class StructuredResume(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    summary: str | None = None
    skills: list[str] = []
    experience: list[ExperienceItem] = []
    education: list[EducationItem] = []
    projects: list[ProjectItem] = []


class ExtractResumeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    raw_text: str = Field(alias="rawText", min_length=1, max_length=50_000)


class ExtractResumeResponse(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    summary: str | None
    skills: list[str]
    experience: list[ExperienceItem]
    education: list[EducationItem]
    projects: list[ProjectItem]
