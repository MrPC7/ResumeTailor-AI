from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings
from schemas.customize_resume import CustomizeResumeRequest, CustomizeResumeResponse
from services.resume_customizer import resume_customizer
from services.resume_customizer.customizer import ResumeCustomizationError
from services.resume_extractor.gemini_client import GeminiAPIError

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/customize-resume", response_model=CustomizeResumeResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def customize_resume(request: Request, body: CustomizeResumeRequest) -> CustomizeResumeResponse:
    try:
        return await resume_customizer.customize(body)
    except GeminiAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again.",
        ) from exc
    except ResumeCustomizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider returned an invalid response. Please try again.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to customize resume.",
        ) from exc
