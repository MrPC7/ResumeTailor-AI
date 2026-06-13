from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings
from schemas.extract_resume import ExtractResumeRequest, ExtractResumeResponse
from services.resume_extractor import resume_extractor
from services.resume_extractor.extractor import ResumeExtractionError
from services.resume_extractor.gemini_client import GeminiAPIError

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/extract-resume", response_model=ExtractResumeResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def extract_resume(request: Request, body: ExtractResumeRequest) -> ExtractResumeResponse:
    try:
        structured = await resume_extractor.extract(body.raw_text)
        return ExtractResumeResponse(**structured.model_dump())
    except GeminiAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ResumeExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to extract resume structure.",
        ) from exc
