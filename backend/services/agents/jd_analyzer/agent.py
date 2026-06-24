"""JD Analyzer agent — deep analysis of job descriptions for agent pipeline."""
from __future__ import annotations

import logging
from typing import Any

from services.agents.base import BaseAgent
from services.llm import LLMClient

logger = logging.getLogger(__name__)


class JDAnalyzerAgentError(Exception):
    """Raised when the JD analyzer agent fails after all retry attempts."""


class JDAnalyzerAgent(BaseAgent):
    """Extracts structured requirements, expectations, and scoring signals
    from a job description for downstream agents to consume."""

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
