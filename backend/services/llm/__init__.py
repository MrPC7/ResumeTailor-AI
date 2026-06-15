"""Shared LLM infrastructure — clients, errors, and a reusable singleton."""
from __future__ import annotations

from core.config import settings
from services.llm.clients import (
    FallbackLLMClient,
    GeminiClient,
    GroqClient,
    LLMAPIError,
    LLMClient,
    LLMParseError,
)

__all__ = [
    "FallbackLLMClient",
    "GeminiClient",
    "GroqClient",
    "LLMAPIError",
    "LLMClient",
    "LLMParseError",
    "llm_client",
]

llm_client = FallbackLLMClient(
    primary=GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
    ),
    secondary=GroqClient(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
    ),
)
