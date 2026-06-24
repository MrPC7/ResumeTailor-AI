"""Pydantic schemas for the multi-agent pipeline v2."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _coerce_str(v: object) -> str:
    """LLM sometimes returns lists or dicts for string fields."""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "; ".join(str(item) for item in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}: {val}" for k, val in v.items())
    if v is None:
        return ""
    return str(v)


# ---------------------------------------------------------------------------
# Candidate Profile — output of ResumeAnalyzerAgent
# ---------------------------------------------------------------------------


class Skill(BaseModel):
    """A single skill extracted from the resume."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    category: str = ""

    @field_validator("name", "category", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class WorkExperience(BaseModel):
    """A single work-experience entry."""

    model_config = ConfigDict(extra="ignore")

    company: str = ""
    position: str = ""
    duration: str = ""
    responsibilities: list[str] = []
    technologies: list[str] = []

    @field_validator("company", "position", "duration", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class Education(BaseModel):
    """A single education entry."""

    model_config = ConfigDict(extra="ignore")

    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    year: str = ""

    @field_validator("institution", "degree", "field_of_study", "year", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class Project(BaseModel):
    """A single project entry."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    description: str = ""
    technologies: list[str] = []
    role: str = ""

    @field_validator("name", "description", "role", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class Certification(BaseModel):
    """A single certification entry."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    issuer: str = ""
    year: str = ""

    @field_validator("name", "issuer", "year", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class CandidateProfile(BaseModel):
    """Structured factual profile extracted from a resume.

    This is the output of the ResumeAnalyzerAgent and serves as input
    to downstream agents in the multi-agent pipeline.
    """

    model_config = ConfigDict(extra="ignore")

    skills: list[Skill] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    total_years_experience: float | None = None
    primary_domain: str = ""

    @field_validator("primary_domain", mode="before")
    @classmethod
    def coerce_domain(cls, v: object) -> str:
        return _coerce_str(v)
