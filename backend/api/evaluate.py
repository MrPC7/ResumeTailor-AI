"""v2 evaluation endpoint — runs the full multi-agent pipeline."""
from fastapi import APIRouter, HTTPException, Request, status

from core.config import limiter, settings
from schemas.evaluate import EvaluateRequest, EvaluateResponse
from services.agents.resume_analyzer import resume_analyzer_agent
from services.agents.jd_analyzer import jd_analyzer_agent
from services.agents.recruiter import recruiter_agent
from services.orchestrator.evaluation_pipeline import (
    EvaluationPipeline,
    PipelineError,
    PipelineInputError,
)

router = APIRouter(tags=["evaluate"])

_pipeline = EvaluationPipeline(
    resume_analyzer=resume_analyzer_agent,
    jd_analyzer=jd_analyzer_agent,
    recruiter=recruiter_agent,
)


@router.post("/evaluate", response_model=EvaluateResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def evaluate(request: Request, body: EvaluateRequest) -> EvaluateResponse:
    try:
        result = await _pipeline.run(
            raw_resume_text=body.raw_resume_text,
            raw_jd_text=body.raw_jd_text,
        )
    except PipelineInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except PipelineError as exc:
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
                else "AI evaluation pipeline returned an invalid response. Please try again."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete evaluation.",
        ) from exc

    return EvaluateResponse(
        candidate_profile=result.candidate_profile,
        job_profile=result.job_profile,
        evaluation=result.evaluation,
    )
