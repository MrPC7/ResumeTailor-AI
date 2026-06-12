from fastapi import APIRouter, HTTPException, status

from schemas.resume_diff import ResumeDiffRequest, ResumeDiffResponse
from services.diff_engine import compute_diff

router = APIRouter()


@router.post("/resume-diff", response_model=ResumeDiffResponse)
async def resume_diff(body: ResumeDiffRequest) -> ResumeDiffResponse:
    try:
        diff = compute_diff(body.original, body.customized)
        return ResumeDiffResponse(diff=diff)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to compute resume diff.",
        ) from exc
