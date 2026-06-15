from core.config import settings
from services.resume_customizer.customizer import ResumeCustomizer
from services.llm import llm_client

__all__ = ["resume_customizer"]

resume_customizer = ResumeCustomizer(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
