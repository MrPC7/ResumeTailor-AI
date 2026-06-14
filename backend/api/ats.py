from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from schemas.ats import ATSAnalyzeRequest, ATSCompareRequest, ATSPotentialRequest
from services.ats import ats_evaluator
from services.ats.ats_evaluator import ATSEvaluationError
from services.ats.ats_models import (
    ATSComparisonResult,
    ATSEvaluationResult,
    PotentialScoreResult,
    RecommendationReport,
)
from services.ats.potential_score_engine import predict_potential_score
from services.ats.recommendation_engine import generate_recommendations

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/analyze", response_model=ATSEvaluationResult)
async def analyze_ats(body: ATSAnalyzeRequest) -> ATSEvaluationResult:
    try:
        return await ats_evaluator.evaluate(body.resume, body.jobDescription)
    except ATSEvaluationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
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
async def compare_ats(body: ATSCompareRequest) -> ATSComparisonResult:
    try:
        return await ats_evaluator.compare(
            body.originalResume, body.customizedResume, body.jobDescription
        )
    except ATSEvaluationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete ATS comparison.",
        ) from exc
