"""v2 suggestions endpoint — generates actionable resume improvement suggestions."""
from fastapi import APIRouter, HTTPException, Request, status

from core.config import limiter, settings
from schemas.suggestions import SuggestionsRequest, SuggestionsResponse
from services.agents.suggestion_generator import suggestion_generator_agent
from services.agents.suggestion_generator.agent import SuggestionGeneratorError

router = APIRouter(tags=["suggestions"])


@router.post("/suggestions", response_model=SuggestionsResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def generate_suggestions(
    request: Request, body: SuggestionsRequest
) -> SuggestionsResponse:
    try:
        report = await suggestion_generator_agent.generate(
            candidate=body.candidate_profile,
            job=body.job_profile,
            evaluation=body.evaluation,
        )
    except SuggestionGeneratorError as exc:
        message = str(exc).lower()
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "api error" in message or "timed out" in message
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(
            status_code=status_code,
            detail=(
                "AI service is temporarily unavailable. Please try again."
                if status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                else "Failed to generate suggestions. Please try again."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate suggestions.",
        ) from exc

    return SuggestionsResponse(suggestions=report)
