from pydantic import BaseModel, ConfigDict

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse


class GenerateCoverLetterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resume: ExtractResumeResponse
    jd: AnalyzeJDResponse


class CoverLetterRaw(BaseModel):
    """Shape returned by the LLM — extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    coverLetter: str
    strengthsHighlighted: list[str] = []
    matchingSkillsUsed: list[str] = []


class GenerateCoverLetterResponse(BaseModel):
    coverLetter: str
    strengthsHighlighted: list[str]
    matchingSkillsUsed: list[str]
