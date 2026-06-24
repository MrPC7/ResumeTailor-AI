"""Resume Analyzer agent — evaluates resume structure and content quality."""
from __future__ import annotations

import logging
from typing import Any

from services.agents.base import BaseAgent
from services.llm import LLMClient

logger = logging.getLogger(__name__)


class ResumeAnalyzerAgentError(Exception):
    """Raised when the resume analyzer agent fails after all retry attempts."""


class ResumeAnalyzerAgent(BaseAgent):
    """Analyzes a parsed resume for structural quality, content gaps, and
    keyword density before any JD-specific evaluation takes place."""

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
