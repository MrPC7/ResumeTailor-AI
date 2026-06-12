from pydantic import BaseModel, ConfigDict

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse


class GapAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resume: ExtractResumeResponse
    jd: AnalyzeJDResponse


class GapAnalysisResponse(BaseModel):
    matchedSkills: list[str]
    missingSkills: list[str]
    recommendations: list[str]
