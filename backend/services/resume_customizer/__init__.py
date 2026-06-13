from core.config import settings
from services.resume_customizer.customizer import ResumeCustomizer
from services.resume_extractor.gemini_client import FallbackLLMClient, GeminiClient, GroqClient

__all__ = ["resume_customizer"]

resume_customizer = ResumeCustomizer(
    client=FallbackLLMClient(
        primary=GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL,
        ),
        secondary=GroqClient(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
        ),
    ),
    max_retries=settings.GEMINI_MAX_RETRIES,
)
