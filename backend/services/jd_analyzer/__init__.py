from core.config import settings
from services.jd_analyzer.analyzer import JDAnalyzer
from services.llm import llm_client

__all__ = ["jd_analyzer"]

jd_analyzer = JDAnalyzer(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
