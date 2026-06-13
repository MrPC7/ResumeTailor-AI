from typing import Literal

from pydantic import BaseModel

from schemas.extract_resume import ExtractResumeResponse


class DiffToken(BaseModel):
    text: str
    status: Literal["added", "removed", "unchanged"]


class DiffItem(BaseModel):
    value: str
    status: Literal["added", "removed", "unchanged"]


class ExperienceDiff(BaseModel):
    company: str
    position: str
    duration: str
    descriptionDiff: list[DiffToken]


class ProjectDiff(BaseModel):
    name: str
    descriptionDiff: list[DiffToken]
    technologies: list[str]


class ResumeDiff(BaseModel):
    nameDiff: list[DiffToken]
    emailDiff: list[DiffToken]
    phoneDiff: list[DiffToken]
    summaryDiff: list[DiffToken]
    skillsDiff: list[DiffItem]
    experienceDiff: list[ExperienceDiff]
    projectsDiff: list[ProjectDiff]


class ResumeDiffRequest(BaseModel):
    original: ExtractResumeResponse
    customized: ExtractResumeResponse


class ResumeDiffResponse(BaseModel):
    diff: ResumeDiff
