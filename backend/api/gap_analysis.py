from fastapi import APIRouter, HTTPException, status

from schemas.gap_analysis import GapAnalysisRequest, GapAnalysisResponse
from services.gap_analyzer import gap_analyzer
from services.gap_analyzer.analyzer import GapAnalysisError

router = APIRouter()


@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis(body: GapAnalysisRequest) -> GapAnalysisResponse:
    try:
        return gap_analyzer.compute(body)
    except GapAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to perform gap analysis.",
        ) from exc
