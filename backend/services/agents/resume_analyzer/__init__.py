from core.config import settings
from services.agents.resume_analyzer.agent import ResumeAnalyzerAgent
from services.llm import llm_client

__all__ = ["resume_analyzer_agent"]

resume_analyzer_agent = ResumeAnalyzerAgent(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
