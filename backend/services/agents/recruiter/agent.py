"""Recruiter agent — evaluates candidate–job fit from a senior recruiter's perspective."""
from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from schemas.agent_models import CandidateProfile, JobProfile, RecruiterEvaluation
from services.agents.base import BaseAgent
from services.llm import LLMAPIError, LLMClient, LLMParseError
from services.prompt_builder import PromptType, prompt_builder

logger = logging.getLogger(__name__)


class RecruiterAgentError(Exception):
    """Raised when the recruiter agent fails after all retry attempts."""


class RecruiterAgent(BaseAgent):
    """Evaluates a candidate against job requirements from a senior
    technical recruiter's perspective.

    Uses evidence-based reasoning: penalizes missing critical skills,
    rewards strong project evidence, and explains every score.
    """

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate candidate against job from context.

        Parameters
        ----------
        context:
            Must contain:
            - 'candidate_profile' (CandidateProfile)
            - 'job_profile' (JobProfile)

        Returns
        -------
        dict with 'recruiter_evaluation' (RecruiterEvaluation instance).
        """
        candidate: CandidateProfile = context["candidate_profile"]
        job: JobProfile = context["job_profile"]
        evaluation = await self.evaluate(candidate, job)
        return {"recruiter_evaluation": evaluation}

    async def evaluate(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
    ) -> RecruiterEvaluation:
        """Evaluate a candidate against job requirements with retry logic."""
        prompt = prompt_builder.build(
            PromptType.RECRUITER_EVALUATION,
            candidate_json=json.dumps(candidate.model_dump(), indent=2),
            job_json=json.dumps(job.model_dump(), indent=2),
        ).to_single_prompt()

        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                raw_json = await self._client.generate_json(prompt)

                # LLM may wrap result in a single top-level key
                if len(raw_json) == 1:
                    only_value = next(iter(raw_json.values()))
                    if isinstance(only_value, dict):
                        raw_json = only_value

                logger.info(
                    "RecruiterAgent response keys (attempt %d): %s",
                    attempt,
                    list(raw_json.keys()),
                )
                return RecruiterEvaluation.model_validate(raw_json)
            except LLMAPIError:
                raise
            except (LLMParseError, ValidationError) as exc:
                logger.warning(
                    "RecruiterAgent attempt %d/%d failed: %s — %s",
                    attempt,
                    self._max_retries,
                    type(exc).__name__,
                    exc,
                )
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise RecruiterAgentError(
            f"Failed to produce recruiter evaluation after {self._max_retries} attempt(s)."
        ) from last_error
