from core.config import settings
from services.cover_letter_generator.generator import CoverLetterGenerator
from services.resume_extractor.gemini_client import FallbackLLMClient, GeminiClient, GroqClient

__all__ = ["cover_letter_generator"]

cover_letter_generator = CoverLetterGenerator(
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
