from __future__ import annotations

import logging

from pydantic import ValidationError

from schemas.extract_resume import StructuredResume
from services.prompt_builder import PromptType, prompt_builder
from services.resume_extractor.gemini_client import (
    GeminiAPIError,
    GeminiParseError,
    LLMClient,
)

logger = logging.getLogger(__name__)


class ResumeExtractionError(Exception):
    """Raised when extraction fails after all retry attempts."""


class ResumeExtractor:
    def __init__(self, client: LLMClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max(1, max_retries)

    async def extract(self, raw_text: str) -> StructuredResume:
        prompt = prompt_builder.build(PromptType.RESUME_EXTRACTION, raw_text=raw_text).to_single_prompt()
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                raw_json = await self._client.generate_json(prompt)

                # Gemini sometimes wraps the result in a top-level key
                if len(raw_json) == 1:
                    only_value = next(iter(raw_json.values()))
                    if isinstance(only_value, dict):
                        raw_json = only_value

                logger.info("Gemini response keys (attempt %d): %s", attempt, list(raw_json.keys()))
                return StructuredResume.model_validate(raw_json)
            except GeminiAPIError:
                raise
            except (GeminiParseError, ValidationError) as exc:
                logger.warning(
                    "Extraction attempt %d/%d failed: %s — %s",
                    attempt, self._max_retries, type(exc).__name__, exc,
                )
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise ResumeExtractionError(
            f"Failed to extract structured resume after {self._max_retries} attempt(s)."
        ) from last_error
