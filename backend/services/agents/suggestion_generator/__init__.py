from core.config import settings
from services.agents.suggestion_generator.agent import SuggestionGeneratorAgent
from services.llm import llm_client

__all__ = ["suggestion_generator_agent"]

suggestion_generator_agent = SuggestionGeneratorAgent(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)
