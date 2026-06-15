from __future__ import annotations

import asyncio
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
    def __init__(self, api_key: str, model_name: str, timeout_seconds: int = 30) -> None:
        self._model: genai.GenerativeModel | None = None
        self._timeout_seconds = max(1, timeout_seconds)

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
            response = await asyncio.wait_for(
                self._model.generate_content_async(prompt),
                timeout=self._timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise LLMAPIError(
                "LLM provider timed out while generating a response."
            ) from exc
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
    def __init__(self, api_key: str, model_name: str, timeout_seconds: int = 30) -> None:
        self._client: groq.AsyncGroq | None = None
        self._model_name = model_name
        self._timeout_seconds = max(1, timeout_seconds)

        if api_key:
            self._client = groq.AsyncGroq(api_key=api_key)

    async def generate_json(self, prompt: str) -> dict[str, object]:
        if self._client is None:
            raise LLMAPIError(
                "GROQ_API_KEY is not configured. Add it to the backend .env file."
            )

        try:
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                ),
                timeout=self._timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise LLMAPIError(
                "LLM provider timed out while generating a response."
            ) from exc
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

    def __init__(self, primary: LLMClient, secondary: LLMClient, api_retries: int = 2) -> None:
        self._primary = primary
        self._secondary = secondary
        self._api_retries = max(1, api_retries)

    @staticmethod
    def _should_retry(error: Exception) -> bool:
        message = str(error).lower()
        non_retryable_signals = (
            "not configured",
            "api key",
            "unauthorized",
            "permission",
            "invalid",
        )
        return not any(signal in message for signal in non_retryable_signals)

    async def _call_with_retries(self, client: LLMClient, prompt: str) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(1, self._api_retries + 1):
            try:
                return await client.generate_json(prompt)
            except LLMParseError:
                # Parsing is deterministic failure for a provider response shape.
                raise
            except LLMAPIError as exc:
                last_error = exc
                if attempt == self._api_retries or not self._should_retry(exc):
                    break
                await asyncio.sleep(min(0.25 * attempt, 1.0))

        if last_error is None:
            raise LLMAPIError("LLM provider failed unexpectedly.")
        raise last_error

    async def generate_json(self, prompt: str) -> dict[str, object]:
        try:
            return await self._call_with_retries(self._primary, prompt)
        except (LLMAPIError, LLMParseError) as primary_error:
            logger.warning(
                "Primary LLM failed (%s); falling back to secondary provider.",
                primary_error,
            )
            try:
                return await self._call_with_retries(self._secondary, prompt)
            except (LLMAPIError, LLMParseError) as fallback_error:
                raise LLMAPIError(
                    f"Both primary and fallback LLM providers failed. "
                    f"Primary: {primary_error}. Fallback: {fallback_error}."
                ) from fallback_error
