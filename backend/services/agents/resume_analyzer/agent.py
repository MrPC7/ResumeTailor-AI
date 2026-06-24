"""Resume Analyzer agent — extracts structured CandidateProfile from raw resume text."""
from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from schemas.agent_models import CandidateProfile
from services.agents.base import BaseAgent
from services.llm import LLMAPIError, LLMClient, LLMParseError
from services.prompt_builder import PromptType, prompt_builder

logger = logging.getLogger(__name__)


class ResumeAnalyzerAgentError(Exception):
    """Raised when the resume analyzer agent fails after all retry attempts."""


class ResumeAnalyzerAgent(BaseAgent):
    """Extracts a structured CandidateProfile from raw resume text.

    This agent performs factual extraction only — no scoring or evaluation.
    It uses the LLM to parse unstructured text into the CandidateProfile schema.
    """

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Extract CandidateProfile from context['raw_resume_text'].

        Parameters
        ----------
        context:
            Must contain 'raw_resume_text' (str).

        Returns
        -------
        dict with 'candidate_profile' (CandidateProfile instance).
        """
        raw_text: str = context["raw_resume_text"]
        profile = await self.extract(raw_text)
        return {"candidate_profile": profile}

    async def extract(self, raw_text: str) -> CandidateProfile:
        """Extract a CandidateProfile from raw resume text with retry logic."""
        prompt = prompt_builder.build(
            PromptType.CANDIDATE_PROFILE_EXTRACTION,
            raw_text=raw_text,
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
                    "ResumeAnalyzerAgent response keys (attempt %d): %s",
                    attempt,
                    list(raw_json.keys()),
                )
                return CandidateProfile.model_validate(raw_json)
            except LLMAPIError:
                raise
            except (LLMParseError, ValidationError) as exc:
                logger.warning(
                    "ResumeAnalyzerAgent attempt %d/%d failed: %s — %s",
                    attempt,
                    self._max_retries,
                    type(exc).__name__,
                    exc,
                )
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise ResumeAnalyzerAgentError(
            f"Failed to extract candidate profile after {self._max_retries} attempt(s)."
        ) from last_error
