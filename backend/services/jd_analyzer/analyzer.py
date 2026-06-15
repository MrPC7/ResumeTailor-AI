from __future__ import annotations

from pydantic import ValidationError

from schemas.analyze_jd import AnalyzedJD
from services.prompt_builder import PromptType, prompt_builder
from services.llm import (
    GeminiAPIError,
    GeminiParseError,
    LLMClient,
)


class JDAnalysisError(Exception):
    """Raised when JD analysis fails after all retry attempts."""


class JDAnalyzer:
    def __init__(self, client: LLMClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max(1, max_retries)

    async def analyze(self, job_description: str) -> AnalyzedJD:
        prompt = prompt_builder.build(PromptType.JD_ANALYSIS, job_description=job_description).to_single_prompt()
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                raw_json = await self._client.generate_json(prompt)
                return AnalyzedJD.model_validate(raw_json)
            except GeminiAPIError:
                # Non-retryable: missing API key, quota exceeded, network failure.
                raise
            except (GeminiParseError, ValidationError) as exc:
                # Retryable: malformed JSON or schema mismatch from Gemini.
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise JDAnalysisError(
            f"Failed to analyze job description after {self._max_retries} attempt(s)."
        ) from last_error
