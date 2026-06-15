from fastapi import APIRouter, HTTPException, Request, status

from core.config import limiter, settings
from schemas.extract_resume import ExtractResumeRequest, ExtractResumeResponse
from services.resume_extractor import resume_extractor
from services.resume_extractor.extractor import ResumeExtractionError
from services.resume_validator import (
    ai_verifier,
    compute_resume_confidence,
    needs_ai_verification,
)
from services.llm import LLMAPIError

router = APIRouter()

_LOW_CONFIDENCE_THRESHOLD = 30


@router.post("/extract-resume", response_model=ExtractResumeResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def extract_resume(request: Request, body: ExtractResumeRequest) -> ExtractResumeResponse:
    try:
        structured = await resume_extractor.extract(body.raw_text)
    except LLMAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again.",
        ) from exc
    except ResumeExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider returned an invalid response. Please try again.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to extract resume structure.",
        ) from exc

    # ── Resume validation (Layer 2 + 3) ──────────────────────────────
    confidence = compute_resume_confidence(structured)

    if confidence < _LOW_CONFIDENCE_THRESHOLD:
        # Very low confidence — reject immediately
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "This document does not appear to be a resume. "
                "We could not identify common resume sections such as "
                "Skills, Experience, or Education. "
                "Please upload a valid resume in PDF or DOCX format."
            ),
        )

    if needs_ai_verification(confidence):
        # Uncertain range — ask AI
        ai_result = await ai_verifier.verify(body.raw_text)
        if not ai_result["isResume"]:
            reason = ai_result.get("reason", "")
            detail = (
                "This document does not appear to be a resume."
                + (f" {reason}" if reason else "")
                + " Please upload a valid resume in PDF or DOCX format."
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=detail,
            )

    return ExtractResumeResponse(**structured.model_dump())
