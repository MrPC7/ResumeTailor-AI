from fastapi import APIRouter, HTTPException, Request, status

from core.config import limiter, settings
from schemas.cover_letter import GenerateCoverLetterRequest, GenerateCoverLetterResponse
from services.cover_letter_generator import cover_letter_generator
from services.cover_letter_generator.generator import CoverLetterGenerationError
from services.llm import LLMAPIError

router = APIRouter()


@router.post("/cover-letter", response_model=GenerateCoverLetterResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def generate_cover_letter(
    request: Request, body: GenerateCoverLetterRequest
) -> GenerateCoverLetterResponse:
    try:
        return await cover_letter_generator.generate(body)
    except LLMAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again.",
        ) from exc
    except CoverLetterGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider returned an invalid response. Please try again.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate cover letter.",
        ) from exc
