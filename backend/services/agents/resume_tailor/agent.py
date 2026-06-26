"""Resume Tailor agent — rewrites resume guided by recruiter evaluation."""
from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    TailoredResume,
)
from services.agents.base import BaseAgent
from services.llm import LLMAPIError, LLMClient, LLMParseError
from services.prompt_builder import PromptType, prompt_builder

logger = logging.getLogger(__name__)


class ResumeTailorAgentError(Exception):
    """Raised when the resume tailor agent fails after all retry attempts."""


class ResumeTailorAgent(BaseAgent):
    """Rewrites resume content to maximize relevance, clarity, and
    recruiter visibility for a specific job.

    Uses the recruiter evaluation to amplify strengths and address gaps
    while strictly preserving factual accuracy and identity.
    """

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Tailor resume using context from previous agents.

        Parameters
        ----------
        context:
            Must contain:
            - 'candidate_profile' (CandidateProfile)
            - 'job_profile' (JobProfile)
            - 'recruiter_evaluation' (RecruiterEvaluation)

        Returns
        -------
        dict with 'tailored_resume' (TailoredResume instance).
        """
        candidate: CandidateProfile = context["candidate_profile"]
        job: JobProfile = context["job_profile"]
        evaluation: RecruiterEvaluation = context["recruiter_evaluation"]
        tailored = await self.tailor(candidate, job, evaluation)
        return {"tailored_resume": tailored}

    async def tailor(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        evaluation: RecruiterEvaluation,
    ) -> TailoredResume:
        """Rewrite resume guided by recruiter evaluation with retry logic."""
        prompt = prompt_builder.build(
            PromptType.RESUME_TAILORING,
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
                    "ResumeTailorAgent response keys (attempt %d): %s",
                    attempt,
                    list(raw_json.keys()),
                )
                return TailoredResume.model_validate(raw_json)
            except LLMAPIError:
                raise
            except (LLMParseError, ValidationError) as exc:
                logger.warning(
                    "ResumeTailorAgent attempt %d/%d failed: %s — %s",
                    attempt,
                    self._max_retries,
                    type(exc).__name__,
                    exc,
                )
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise ResumeTailorAgentError(
            f"Failed to tailor resume after {self._max_retries} attempt(s)."
        ) from last_error
