"""Pydantic schemas for the multi-agent pipeline v2."""
from __future__ import annotations

from typing import Literal

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


# ---------------------------------------------------------------------------
# Job Profile — output of JDAnalyzerAgent
# ---------------------------------------------------------------------------

SENIORITY_LEVELS = Literal[
    "Intern",
    "Junior",
    "Mid",
    "Senior",
    "Lead",
    "Principal",
    "Staff",
    "Director",
    "VP",
    "C-Level",
]


class RequiredSkill(BaseModel):
    """A must-have skill extracted from the job description."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    category: str = ""

    @field_validator("name", "category", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class PreferredSkill(BaseModel):
    """A nice-to-have skill extracted from the job description."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    category: str = ""

    @field_validator("name", "category", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class Responsibility(BaseModel):
    """A single responsibility or duty from the job description."""

    model_config = ConfigDict(extra="ignore")

    description: str = ""
    priority: Literal["high", "medium", "low"] = "medium"

    @field_validator("description", mode="before")
    @classmethod
    def coerce_description(cls, v: object) -> str:
        return _coerce_str(v)

    @field_validator("priority", mode="before")
    @classmethod
    def coerce_priority(cls, v: object) -> str:
        if isinstance(v, str) and v.lower() in ("high", "medium", "low"):
            return v.lower()
        return "medium"


class ExperienceRequirement(BaseModel):
    """Structured experience requirement from the JD."""

    model_config = ConfigDict(extra="ignore")

    min_years: float | None = None
    max_years: float | None = None
    domain: str = ""

    @field_validator("domain", mode="before")
    @classmethod
    def coerce_domain(cls, v: object) -> str:
        return _coerce_str(v)

    @field_validator("min_years", "max_years", mode="before")
    @classmethod
    def coerce_years(cls, v: object) -> float | None:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v.strip().rstrip("+"))
            except ValueError:
                return None
        return None


class JobProfile(BaseModel):
    """Structured job profile extracted from a job description.

    This is the output of the JDAnalyzerAgent and serves as input
    to downstream agents (Recruiter, Tailor, Reevaluator).
    """

    model_config = ConfigDict(extra="ignore")

    role: str = ""
    seniority: str = ""
    must_have_skills: list[RequiredSkill] = Field(default_factory=list)
    preferred_skills: list[PreferredSkill] = Field(default_factory=list)
    responsibilities: list[Responsibility] = Field(default_factory=list)
    experience_required: ExperienceRequirement = Field(
        default_factory=ExperienceRequirement
    )

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, v: object) -> str:
        return _coerce_str(v)

    @field_validator("seniority", mode="before")
    @classmethod
    def coerce_seniority(cls, v: object) -> str:
        """Coerce and validate seniority to one of the allowed levels."""
        raw = _coerce_str(v).strip().title()
        allowed = {
            "Intern", "Junior", "Mid", "Senior", "Lead",
            "Principal", "Staff", "Director", "Vp", "C-Level",
        }
        # Normalize common variants
        mapping = {
            "Vp": "VP",
            "C-Level": "C-Level",
            "C Level": "C-Level",
            "Entry": "Junior",
            "Entry Level": "Junior",
            "Middle": "Mid",
            "Sr": "Senior",
            "Sr.": "Senior",
        }
        normalized = mapping.get(raw, raw)
        if normalized in ("VP",):
            return normalized
        if normalized.replace("-", "").replace(" ", "") in {
            a.replace("-", "").replace(" ", "") for a in allowed
        }:
            return normalized
        # Default to empty if unrecognizable — deterministic, no guessing
        return raw if raw else ""


# ---------------------------------------------------------------------------
# Recruiter Evaluation — output of RecruiterAgent
# ---------------------------------------------------------------------------

MATCH_LEVELS = Literal["strong_match", "good_match", "partial_match", "weak_match", "no_match"]


class RecruiterEvaluation(BaseModel):
    """Structured recruiter evaluation of a candidate against a job profile.

    This is the output of the RecruiterAgent and feeds into the
    ResumeTailorAgent and ReevaluatorAgent downstream.
    """

    model_config = ConfigDict(extra="ignore")

    match_level: str = ""
    hiring_confidence: int = Field(default=0, ge=0, le=100)
    interview_probability: int = Field(default=0, ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    verdict: str = ""
    reasoning: list[str] = Field(default_factory=list)

    @field_validator("match_level", mode="before")
    @classmethod
    def coerce_match_level(cls, v: object) -> str:
        raw = _coerce_str(v).strip().lower().replace(" ", "_")
        valid = {"strong_match", "good_match", "partial_match", "weak_match", "no_match"}
        return raw if raw in valid else _coerce_str(v).strip().lower()

    @field_validator("verdict", mode="before")
    @classmethod
    def coerce_verdict(cls, v: object) -> str:
        return _coerce_str(v)

    @field_validator("hiring_confidence", "interview_probability", mode="before")
    @classmethod
    def coerce_score(cls, v: object) -> int:
        if isinstance(v, int):
            return max(0, min(100, v))
        if isinstance(v, float):
            return max(0, min(100, int(v)))
        if isinstance(v, str):
            try:
                return max(0, min(100, int(float(v.strip().rstrip("%")))))
            except ValueError:
                return 0
        return 0


# ---------------------------------------------------------------------------
# Tailored Resume — output of ResumeTailorAgent
# ---------------------------------------------------------------------------


class TailoredExperience(BaseModel):
    """A rewritten work-experience entry optimized for the target role."""

    model_config = ConfigDict(extra="ignore")

    company: str = ""
    position: str = ""
    duration: str = ""
    description: str = ""
    technologies: list[str] = []

    @field_validator("company", "position", "duration", "description", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class TailoredProject(BaseModel):
    """A rewritten project entry optimized for the target role."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    description: str = ""
    technologies: list[str] = []

    @field_validator("name", "description", mode="before")
    @classmethod
    def coerce_strings(cls, v: object) -> str:
        return _coerce_str(v)


class TailoredResume(BaseModel):
    """Structured output of the ResumeTailorAgent.

    Contains the rewritten resume optimized for the target role based on
    recruiter evaluation gaps and strengths.
    """

    model_config = ConfigDict(extra="ignore")

    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[TailoredExperience] = Field(default_factory=list)
    projects: list[TailoredProject] = Field(default_factory=list)
    improvements_made: list[str] = Field(default_factory=list)
    gaps_addressed: list[str] = Field(default_factory=list)

    @field_validator("summary", mode="before")
    @classmethod
    def coerce_summary(cls, v: object) -> str:
        return _coerce_str(v)
