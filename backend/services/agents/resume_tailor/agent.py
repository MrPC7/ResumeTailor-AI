"""Resume Tailor agent — rewrites resume sections to maximize JD fit."""
from __future__ import annotations

import logging
from typing import Any

from services.agents.base import BaseAgent
from services.llm import LLMClient

logger = logging.getLogger(__name__)


class ResumeTailorAgentError(Exception):
    """Raised when the resume tailor agent fails after all retry attempts."""


class ResumeTailorAgent(BaseAgent):
    """Takes recruiter feedback and JD analysis to rewrite resume sections,
    preserving identity and factual accuracy while improving ATS alignment."""

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
