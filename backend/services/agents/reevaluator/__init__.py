from core.config import settings
from services.agents.reevaluator.agent import ReevaluatorAgent
from services.llm import llm_client

__all__ = ["reevaluator_agent"]

reevaluator_agent = ReevaluatorAgent(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
