from fastapi import APIRouter, HTTPException, status

from schemas.match_score import MatchScoreRequest, MatchScoreResponse
from services.match_engine import match_engine
from services.match_engine.engine import MatchEngineError

router = APIRouter()


@router.post("/match-score", response_model=MatchScoreResponse)
async def get_match_score(body: MatchScoreRequest) -> MatchScoreResponse:
    try:
        return match_engine.compute(body)
    except MatchEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to compute ATS match score.",
        ) from exc
