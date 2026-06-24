from core.config import settings
from services.agents.jd_analyzer.agent import JDAnalyzerAgent
from services.llm import llm_client

__all__ = ["jd_analyzer_agent"]

jd_analyzer_agent = JDAnalyzerAgent(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
