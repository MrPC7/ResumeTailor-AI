from fastapi import APIRouter, File, HTTPException, UploadFile, status

from schemas.parse_resume import ParseResumeResponse
from services.parse_resume_service import ResumeParseValidationError, resume_parse_service

router = APIRouter()


@router.post("/parse-resume", response_model=ParseResumeResponse)
async def parse_resume(file: UploadFile = File(...)) -> ParseResumeResponse:
    try:
        raw_text = await resume_parse_service.parse_resume(file)
        return ParseResumeResponse(raw_text=raw_text)
    except ResumeParseValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to parse resume.",
        ) from exc
