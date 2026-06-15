from __future__ import annotations

import json

from pydantic import ValidationError

from schemas.cover_letter import (
    CoverLetterRaw,
    GenerateCoverLetterRequest,
    GenerateCoverLetterResponse,
)
from services.prompt_builder import PromptType, prompt_builder
from services.llm import (
    LLMAPIError,
    LLMParseError,
    LLMClient,
)


class CoverLetterGenerationError(Exception):
    """Raised when cover letter generation fails after all retry attempts."""


class CoverLetterGenerator:
    def __init__(self, client: LLMClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max(1, max_retries)

    async def generate(self, payload: GenerateCoverLetterRequest) -> GenerateCoverLetterResponse:
        resume_json = json.dumps(payload.resume.model_dump(), indent=2)
        jd_json = json.dumps(payload.jd.model_dump(), indent=2)

        prompt = prompt_builder.build(
            PromptType.COVER_LETTER,
            resume_json=resume_json,
            jd_json=jd_json,
        ).to_single_prompt()

        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                raw_json = await self._client.generate_json(prompt)
                validated = CoverLetterRaw.model_validate(raw_json)
                return GenerateCoverLetterResponse(
                    coverLetter=validated.coverLetter,
                    strengthsHighlighted=validated.strengthsHighlighted,
                    matchingSkillsUsed=validated.matchingSkillsUsed,
                )
            except LLMAPIError:
                raise
            except (LLMParseError, ValidationError) as exc:
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise CoverLetterGenerationError(
            f"Failed to generate cover letter after {self._max_retries} attempt(s)."
        ) from last_error
