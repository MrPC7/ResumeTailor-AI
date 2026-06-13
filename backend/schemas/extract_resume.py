from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _coerce_str(v: object) -> str:
    """Gemini sometimes returns lists or dicts for string fields."""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "; ".join(str(item) for item in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}: {val}" for k, val in v.items())
    if v is None:
        return ""
    return str(v)


class ExperienceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company: str = ""
    position: str = ""
    duration: str = ""
    description: str = ""

    @field_validator("company", "position", "duration", "description", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class EducationItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    institution: str = ""
    degree: str = ""
    year: str = ""

    @field_validator("institution", "degree", "year", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class ProjectItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = ""
    description: str = ""
    technologies: list[str] = []

    @field_validator("name", "description", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


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

    @field_validator("name", "email", "phone", "summary", mode="before")
    @classmethod
    def coerce_optional_strings(cls, v: object) -> str | None:
        if v is None:
            return None
        return _coerce_str(v)


class ExtractResumeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    raw_text: str = Field(alias="rawText", min_length=1, max_length=100_000)


class ExtractResumeResponse(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    summary: str | None
    skills: list[str]
    experience: list[ExperienceItem]
    education: list[EducationItem]
    projects: list[ProjectItem]
