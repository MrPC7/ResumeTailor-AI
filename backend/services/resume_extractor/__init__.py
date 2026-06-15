from core.config import settings
from services.resume_extractor.extractor import ResumeExtractor
from services.llm import llm_client

__all__ = ["resume_extractor"]

resume_extractor = ResumeExtractor(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
