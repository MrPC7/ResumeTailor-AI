"""Re-evaluation endpoint — compares original vs optimized resume against a JD."""
from fastapi import APIRouter, HTTPException, Request, status

from core.config import limiter, settings
from schemas.reevaluate import ReevaluateRequest, ReevaluateResponse
from services.agents.resume_analyzer import resume_analyzer_agent
from services.agents.jd_analyzer import jd_analyzer_agent
from services.agents.recruiter import recruiter_agent
from services.orchestrator.reevaluation_pipeline import (
    ReevaluationPipeline,
    ReevaluationInputError,
    ReevaluationPipelineError,
    ReevaluationTimeoutError,
)

router = APIRouter(tags=["reevaluate"])

_pipeline = ReevaluationPipeline(
    resume_analyzer=resume_analyzer_agent,
    jd_analyzer=jd_analyzer_agent,
    recruiter=recruiter_agent,
)


@router.post("/reevaluate", response_model=ReevaluateResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def reevaluate(request: Request, body: ReevaluateRequest) -> ReevaluateResponse:
    try:
        result = await _pipeline.run(
            original_resume_text=body.original_resume_text,
            optimized_resume_text=body.optimized_resume_text,
            raw_jd_text=body.raw_jd_text,
        )
    except ReevaluationInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ReevaluationTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Re-evaluation timed out. Please try again.",
        ) from exc
    except ReevaluationPipelineError as exc:
        message = str(exc).lower()
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "api error" in message or "timed out" in message or "provider" in message
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(
            status_code=status_code,
            detail=(
                "AI service is temporarily unavailable. Please try again."
                if status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                else "AI re-evaluation pipeline returned an invalid response. Please try again."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete re-evaluation.",
        ) from exc

    return ReevaluateResponse(
        before=result.before,
        after=result.after,
        improvement=result.improvement,
    )
