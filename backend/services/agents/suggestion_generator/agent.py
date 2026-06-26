"""Suggestion Generator agent — produces actionable resume improvement suggestions."""
from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    SuggestionReport,
)
from services.agents.base import BaseAgent
from services.llm import LLMAPIError, LLMClient, LLMParseError
from services.prompt_builder import PromptType, prompt_builder

logger = logging.getLogger(__name__)


class SuggestionGeneratorError(Exception):
    """Raised when suggestion generation fails after all retry attempts."""


class SuggestionGeneratorAgent(BaseAgent):
    """Generates actionable, evidence-based resume improvement suggestions.

    Uses the recruiter evaluation gaps and strengths to produce independent,
    selectable suggestions that the user can apply to their resume.
    Does NOT rewrite the resume — only suggests what to change.
    """

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate suggestions from pipeline context.

        Parameters
        ----------
        context:
            Must contain:
            - 'candidate_profile' (CandidateProfile)
            - 'job_profile' (JobProfile)
            - 'recruiter_evaluation' (RecruiterEvaluation)

        Returns
        -------
        dict with 'suggestion_report' (SuggestionReport instance).
        """
        candidate: CandidateProfile = context["candidate_profile"]
        job: JobProfile = context["job_profile"]
        evaluation: RecruiterEvaluation = context["recruiter_evaluation"]
        report = await self.generate(candidate, job, evaluation)
        return {"suggestion_report": report}

    async def generate(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        evaluation: RecruiterEvaluation,
    ) -> SuggestionReport:
        """Generate suggestions with retry logic."""
        prompt = prompt_builder.build(
            PromptType.SUGGESTION_GENERATION,
            candidate_json=json.dumps(candidate.model_dump(), indent=2),
            job_json=json.dumps(job.model_dump(), indent=2),
            evaluation_json=json.dumps(evaluation.model_dump(), indent=2),
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
                    "SuggestionGeneratorAgent response keys (attempt %d): %s",
                    attempt,
                    list(raw_json.keys()),
                )
                return SuggestionReport.model_validate(raw_json)
            except LLMAPIError:
                raise
            except (LLMParseError, ValidationError) as exc:
                logger.warning(
                    "SuggestionGeneratorAgent attempt %d/%d failed: %s — %s",
                    attempt,
                    self._max_retries,
                    type(exc).__name__,
                    exc,
                )
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise SuggestionGeneratorError(
            f"Failed to generate suggestions after {self._max_retries} attempt(s)."
        ) from last_error
