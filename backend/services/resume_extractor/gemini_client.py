from __future__ import annotations

import json

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError


class GeminiAPIError(Exception):
    """Raised on Gemini API-level failures. Not retried."""


class GeminiParseError(Exception):
    """Raised when response text cannot be decoded as JSON. Retried."""


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
            raise GeminiAPIError(
                "GEMINI_API_KEY is not configured. Add it to the backend .env file."
            )

        try:
            response = await self._model.generate_content_async(prompt)
        except GoogleAPIError as exc:
            raise GeminiAPIError(str(exc)) from exc

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise GeminiParseError("Gemini returned non-JSON content.") from exc
