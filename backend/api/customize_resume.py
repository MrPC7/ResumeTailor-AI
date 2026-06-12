from fastapi import APIRouter, HTTPException, status

from schemas.customize_resume import CustomizeResumeRequest, CustomizeResumeResponse
from services.resume_customizer import resume_customizer
from services.resume_customizer.customizer import ResumeCustomizationError
from services.resume_extractor.gemini_client import GeminiAPIError

router = APIRouter()


@router.post("/customize-resume", response_model=CustomizeResumeResponse)
async def customize_resume(body: CustomizeResumeRequest) -> CustomizeResumeResponse:
    try:
        return await resume_customizer.customize(body)
    except GeminiAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ResumeCustomizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to customize resume.",
        ) from exc
