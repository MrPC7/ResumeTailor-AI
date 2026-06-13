from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse


class ATSAnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resume: ExtractResumeResponse
    jobDescription: AnalyzeJDResponse


class ATSCompareRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    originalResume: ExtractResumeResponse
    customizedResume: ExtractResumeResponse
    jobDescription: AnalyzeJDResponse
