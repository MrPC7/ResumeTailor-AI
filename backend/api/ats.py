from fastapi import APIRouter, HTTPException, Request, status

from core.config import limiter, settings
from schemas.ats import ATSAnalyzeRequest, ATSCompareRequest, ATSPotentialRequest
from services.ats import ats_evaluator
from services.ats.ats_evaluator import ATSEvaluationError
from schemas.ats_models import (
    ATSComparisonResult,
    ATSEvaluationResult,
    PotentialScoreResult,
    RecommendationReport,
)
from services.ats.potential_score_engine import predict_potential_score
from services.ats.recommendation_engine import generate_recommendations

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/analyze", response_model=ATSEvaluationResult)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def analyze_ats(request: Request, body: ATSAnalyzeRequest) -> ATSEvaluationResult:
    try:
        return await ats_evaluator.evaluate(body.resume, body.jobDescription)
    except ATSEvaluationError as exc:
        message = str(exc).lower()
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "api error" in message or "timed out" in message or "provider" in message
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(
            status_code=status_code,
            detail=(
                "AI service is temporarily unavailable. Please try again."
                if status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                else "AI provider returned an invalid response. Please try again."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete ATS analysis.",
        ) from exc


@router.post("/potential", response_model=PotentialScoreResult)
async def predict_ats_potential(body: ATSPotentialRequest) -> PotentialScoreResult:
    try:
        return predict_potential_score(body.evaluation, body.resume, body.jobDescription)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to predict potential score.",
        ) from exc


@router.post("/recommendations", response_model=RecommendationReport)
async def get_recommendations(body: ATSPotentialRequest) -> RecommendationReport:
    try:
        return generate_recommendations(body.evaluation, body.resume, body.jobDescription)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate recommendations.",
        ) from exc


@router.post("/compare", response_model=ATSComparisonResult)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def compare_ats(request: Request, body: ATSCompareRequest) -> ATSComparisonResult:
    try:
        return await ats_evaluator.compare(
            body.originalResume, body.customizedResume, body.jobDescription
        )
    except ATSEvaluationError as exc:
        message = str(exc).lower()
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "api error" in message or "timed out" in message or "provider" in message
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(
            status_code=status_code,
            detail=(
                "AI service is temporarily unavailable. Please try again."
                if status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                else "AI provider returned an invalid response. Please try again."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete ATS comparison.",
        ) from exc
