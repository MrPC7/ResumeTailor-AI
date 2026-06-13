from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from schemas.ats import ATSAnalyzeRequest, ATSCompareRequest
from services.ats import ats_engine
from services.ats.ats_engine import ATSEngineError
from services.ats.models import ATSAnalysisResult, ATSComparisonResult

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/analyze", response_model=ATSAnalysisResult)
async def analyze_ats(body: ATSAnalyzeRequest) -> ATSAnalysisResult:
    try:
        return ats_engine.analyze(body.resume, body.jobDescription)
    except ATSEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete ATS analysis.",
        ) from exc


@router.post("/compare", response_model=ATSComparisonResult)
async def compare_ats(body: ATSCompareRequest) -> ATSComparisonResult:
    try:
        return ats_engine.compare(
            body.originalResume, body.customizedResume, body.jobDescription
        )
    except ATSEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete ATS comparison.",
        ) from exc
