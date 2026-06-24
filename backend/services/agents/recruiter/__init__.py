from core.config import settings
from services.agents.recruiter.agent import RecruiterAgent
from services.llm import llm_client

__all__ = ["recruiter_agent"]

recruiter_agent = RecruiterAgent(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
