"""JD Analyzer agent — extracts structured JobProfile from raw job description text."""
from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from schemas.agent_models import JobProfile
from services.agents.base import BaseAgent
from services.llm import LLMAPIError, LLMClient, LLMParseError
from services.prompt_builder import PromptType, prompt_builder

logger = logging.getLogger(__name__)


class JDAnalyzerAgentError(Exception):
    """Raised when the JD analyzer agent fails after all retry attempts."""


class JDAnalyzerAgent(BaseAgent):
    """Extracts a structured JobProfile from raw job description text.

    This agent performs factual extraction only — no candidate evaluation.
    It uses the LLM to parse unstructured JD text into the JobProfile schema.
    """

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Extract JobProfile from context['raw_jd_text'].

        Parameters
        ----------
        context:
            Must contain 'raw_jd_text' (str).

        Returns
        -------
        dict with 'job_profile' (JobProfile instance).
        """
        raw_jd: str = context["raw_jd_text"]
        profile = await self.extract(raw_jd)
        return {"job_profile": profile}

    async def extract(self, job_description: str) -> JobProfile:
        """Extract a JobProfile from raw JD text with retry logic."""
        prompt = prompt_builder.build(
            PromptType.JOB_PROFILE_EXTRACTION,
            job_description=job_description,
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
                    "JDAnalyzerAgent response keys (attempt %d): %s",
                    attempt,
                    list(raw_json.keys()),
                )
                return JobProfile.model_validate(raw_json)
            except LLMAPIError:
                raise
            except (LLMParseError, ValidationError) as exc:
                logger.warning(
                    "JDAnalyzerAgent attempt %d/%d failed: %s — %s",
                    attempt,
                    self._max_retries,
                    type(exc).__name__,
                    exc,
                )
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise JDAnalyzerAgentError(
            f"Failed to extract job profile after {self._max_retries} attempt(s)."
        ) from last_error
