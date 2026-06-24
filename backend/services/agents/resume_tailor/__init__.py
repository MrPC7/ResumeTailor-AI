from core.config import settings
from services.agents.resume_tailor.agent import ResumeTailorAgent
from services.llm import llm_client

__all__ = ["resume_tailor_agent"]

resume_tailor_agent = ResumeTailorAgent(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
