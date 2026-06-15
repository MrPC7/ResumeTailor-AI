from core.config import settings
from services.cover_letter_generator.generator import CoverLetterGenerator
from services.llm import llm_client

__all__ = ["cover_letter_generator"]

cover_letter_generator = CoverLetterGenerator(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
