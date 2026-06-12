from fastapi import APIRouter, HTTPException, status

from schemas.analyze_jd import AnalyzeJDRequest, AnalyzeJDResponse
from services.jd_analyzer import jd_analyzer
from services.jd_analyzer.analyzer import JDAnalysisError
from services.resume_extractor.gemini_client import GeminiAPIError

router = APIRouter()


@router.post("/analyze-jd", response_model=AnalyzeJDResponse)
async def analyze_jd(body: AnalyzeJDRequest) -> AnalyzeJDResponse:
    try:
        result = await jd_analyzer.analyze(body.job_description)
        return AnalyzeJDResponse(
            role=result.role,
            seniority=result.seniority,
            requiredSkills=result.required_skills,
            preferredSkills=result.preferred_skills,
            atsKeywords=result.ats_keywords,
            responsibilities=result.responsibilities,
        )
    except GeminiAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except JDAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyze job description.",
        ) from exc
