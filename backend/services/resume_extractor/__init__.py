from core.config import settings
from services.resume_extractor.extractor import ResumeExtractor
from services.resume_extractor.gemini_client import GeminiClient

__all__ = ["resume_extractor"]

resume_extractor = ResumeExtractor(
    client=GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL,
    ),
    max_retries=settings.GEMINI_MAX_RETRIES,
)
