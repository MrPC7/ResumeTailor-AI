from __future__ import annotations

import json
import logging
from typing import Protocol, runtime_checkable

import google.generativeai as genai
import groq
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared error types
# ---------------------------------------------------------------------------


class LLMAPIError(Exception):
    """Raised when all LLM providers fail with API-level errors."""


class LLMParseError(Exception):
    """Raised when an LLM response cannot be decoded as JSON. Retried."""


# Aliases so existing code that catches GeminiAPIError / GeminiParseError still works.
GeminiAPIError = LLMAPIError
GeminiParseError = LLMParseError


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMClient(Protocol):
    """Minimal interface shared by all LLM provider clients."""

    async def generate_json(self, prompt: str) -> dict[str, object]:
        ...


# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------


class GeminiClient:
    def __init__(self, api_key: str, model_name: str) -> None:
        self._model: genai.GenerativeModel | None = None

        if api_key:
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=genai.GenerationConfig(
                    # Forces the model to emit valid JSON every time.
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

    async def generate_json(self, prompt: str) -> dict[str, object]:
        if self._model is None:
            raise LLMAPIError(
                "GEMINI_API_KEY is not configured. Add it to the backend .env file."
            )

        try:
            response = await self._model.generate_content_async(prompt)
        except GoogleAPIError as exc:
            raise LLMAPIError(str(exc)) from exc

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise LLMParseError("Gemini returned non-JSON content.") from exc


# ---------------------------------------------------------------------------
# Groq client
# ---------------------------------------------------------------------------


class GroqClient:
    def __init__(self, api_key: str, model_name: str) -> None:
        self._client: groq.AsyncGroq | None = None
        self._model_name = model_name

        if api_key:
            self._client = groq.AsyncGroq(api_key=api_key)

    async def generate_json(self, prompt: str) -> dict[str, object]:
        if self._client is None:
            raise LLMAPIError(
                "GROQ_API_KEY is not configured. Add it to the backend .env file."
            )

        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
        except groq.APIError as exc:
            raise LLMAPIError(str(exc)) from exc

        text = response.choices[0].message.content or ""
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMParseError("Groq returned non-JSON content.") from exc


# ---------------------------------------------------------------------------
# Fallback client: primary → secondary on API error
# ---------------------------------------------------------------------------


class FallbackLLMClient:
    """Tries the primary client first; falls back to the secondary on LLMAPIError."""

    def __init__(self, primary: LLMClient, secondary: LLMClient) -> None:
        self._primary = primary
        self._secondary = secondary

    async def generate_json(self, prompt: str) -> dict[str, object]:
        try:
            return await self._primary.generate_json(prompt)
        except (LLMAPIError, LLMParseError) as primary_error:
            logger.warning(
                "Primary LLM failed (%s); falling back to secondary provider.",
                primary_error,
            )
            try:
                return await self._secondary.generate_json(prompt)
            except (LLMAPIError, LLMParseError) as fallback_error:
                raise LLMAPIError(
                    f"Both primary and fallback LLM providers failed. "
                    f"Primary: {primary_error}. Fallback: {fallback_error}."
                ) from fallback_error
