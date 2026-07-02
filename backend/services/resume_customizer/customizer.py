from __future__ import annotations

import json

from pydantic import ValidationError

from schemas.customize_resume import CustomizeResumeRaw, CustomizeResumeRequest, CustomizeResumeResponse
from schemas.extract_resume import ExtractResumeResponse
from services.prompt_builder import PromptType, prompt_builder
from services.llm import (
    LLMAPIError,
    LLMParseError,
    LLMClient,
)
from services.resume_customizer.length_guard import (
    compress_resume,
    estimate_pdf_overflow,
    measure_resume,
    needs_compression,
)


class ResumeCustomizationError(Exception):
    """Raised when customization fails after all retry attempts."""


class ResumeCustomizer:
    def __init__(self, client: LLMClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max(1, max_retries)

    @staticmethod
    def _to_response(raw: CustomizeResumeRaw, original: ExtractResumeResponse, compressed: bool = False) -> CustomizeResumeResponse:
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
            compressed=compressed,
        )

    async def customize(self, payload: CustomizeResumeRequest) -> CustomizeResumeResponse:
        resume_json = json.dumps(payload.resume.model_dump(), indent=2)
        jd_json = json.dumps(payload.jd.model_dump(), indent=2)
        selected_ids = set(payload.selected_suggestion_ids)
        selected_suggestions = [
            suggestion.model_dump()
            for suggestion in payload.suggestions
            if suggestion.id in selected_ids
        ]
        unselected_ids = [
            suggestion.id
            for suggestion in payload.suggestions
            if suggestion.id not in selected_ids
        ]
        accepted_json = json.dumps(selected_suggestions, indent=2)
        rejected_json = json.dumps(unselected_ids, indent=2)

        if not selected_suggestions:
            return CustomizeResumeResponse(
                customizedResume=payload.resume,
                suggestions=[],
                compressed=False,
            )

        prompt = prompt_builder.build(
            PromptType.RESUME_CUSTOMIZATION,
            resume_json=resume_json,
            jd_json=jd_json,
            accepted_json=accepted_json,
            rejected_json=rejected_json,
            selected_suggestion_ids_json=json.dumps(payload.selected_suggestion_ids, indent=2),
        ).to_single_prompt()

        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                raw_json = await self._client.generate_json(prompt)
                validated = CustomizeResumeRaw.model_validate(raw_json)
                response = self._to_response(validated, payload.resume)

                # Length guard: compress if customized resume is too long
                original_metrics = measure_resume(payload.resume)
                customized_metrics = measure_resume(response.customizedResume)
                compressed = False

                if needs_compression(original_metrics, customized_metrics) or estimate_pdf_overflow(response.customizedResume):
                    response.customizedResume = await compress_resume(self._client, response.customizedResume)
                    compressed = True

                response.compressed = compressed
                return response
            except LLMAPIError:
                # Non-retryable: missing API key, quota exceeded, network failure.
                raise
            except (LLMParseError, ValidationError) as exc:
                # Retryable: malformed JSON or schema mismatch from Gemini.
                last_error = exc
                if attempt == self._max_retries:
                    break

        raise ResumeCustomizationError(
            f"Failed to customize resume after {self._max_retries} attempt(s)."
        ) from last_error
