from __future__ import annotations

from core.config import settings
from services.ats.ats_evaluator import ATSEvaluator
from services.resume_extractor.gemini_client import FallbackLLMClient, GeminiClient, GroqClient

ats_evaluator = ATSEvaluator(
    client=FallbackLLMClient(
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
    ),
    max_retries=settings.GEMINI_MAX_RETRIES,
)

__all__ = ["ats_evaluator"]
