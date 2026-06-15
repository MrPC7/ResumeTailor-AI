from fastapi import APIRouter, HTTPException, Request, status

from core.config import limiter, settings
from schemas.analyze_jd import AnalyzeJDRequest, AnalyzeJDResponse
from services.jd_analyzer import jd_analyzer
from services.jd_analyzer.analyzer import JDAnalysisError
from services.llm import LLMAPIError

router = APIRouter()


@router.post("/analyze-jd", response_model=AnalyzeJDResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def analyze_jd(request: Request, body: AnalyzeJDRequest) -> AnalyzeJDResponse:
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
    except LLMAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again.",
        ) from exc
    except JDAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider returned an invalid response. Please try again.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyze job description.",
        ) from exc
