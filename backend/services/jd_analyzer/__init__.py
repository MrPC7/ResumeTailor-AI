from core.config import settings
from services.jd_analyzer.analyzer import JDAnalyzer
from services.resume_extractor.gemini_client import GeminiClient

__all__ = ["jd_analyzer"]

jd_analyzer = JDAnalyzer(
    client=GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL,
    ),
    max_retries=settings.GEMINI_MAX_RETRIES,
)
