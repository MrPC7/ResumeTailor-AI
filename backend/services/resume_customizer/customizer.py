from __future__ import annotations

import json

from pydantic import ValidationError

from schemas.customize_resume import CustomizeResumeRaw, CustomizeResumeRequest, CustomizeResumeResponse
from schemas.extract_resume import ExtractResumeResponse
from services.prompt_builder import PromptType, prompt_builder
from services.resume_extractor.gemini_client import (
    GeminiAPIError,
    GeminiParseError,
    LLMClient,
)


class ResumeCustomizationError(Exception):
    """Raised when customization fails after all retry attempts."""


class ResumeCustomizer:
    def __init__(self, client: LLMClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max(1, max_retries)

    @staticmethod
    def _to_response(raw: CustomizeResumeRaw, original: ExtractResumeResponse) -> CustomizeResumeResponse:
        cr = raw.customizedResume

        # Preserve immutable identity fields from the original to prevent LLM drift.
        customized = ExtractResumeResponse(
            name=original.name,
            email=original.email,
            phone=original.phone,
            summary=cr.summary if cr.summary else original.summary,
            skills=cr.skills if cr.skills else original.skills,
            experience=cr.experience if cr.experience else original.experience,
            education=original.education,
            projects=cr.projects if cr.projects else original.projects,
        )
        return CustomizeResumeResponse(
            customizedResume=customized,
            suggestions=raw.suggestions,
        )

    async def customize(self, payload: CustomizeResumeRequest) -> CustomizeResumeResponse:
        resume_json = json.dumps(payload.resume.model_dump(), indent=2)
        jd_json = json.dumps(payload.jd.model_dump(), indent=2)
        accepted_json = json.dumps(payload.accepted_recommendations, indent=2)
        rejected_json = json.dumps(payload.rejected_recommendations, indent=2)

        prompt = prompt_builder.build(
            PromptType.RESUME_CUSTOMIZATION,
            resume_json=resume_json,
            jd_json=jd_json,
            accepted_json=accepted_json,
            rejected_json=rejected_json,
        ).to_single_prompt()

        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                raw_json = await self._client.generate_json(prompt)
                validated = CustomizeResumeRaw.model_validate(raw_json)
                return self._to_response(validated, payload.resume)
            except GeminiAPIError:
                # Non-retryable: missing API key, quota exceeded, network failure.
                raise
            except (GeminiParseError, ValidationError) as exc:
                # Retryable: malformed JSON or schema mismatch from Gemini.
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise ResumeCustomizationError(
            f"Failed to customize resume after {self._max_retries} attempt(s)."
        ) from last_error
