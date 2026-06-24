"""Recruiter agent — simulates recruiter perspective on resume–JD fit."""
from __future__ import annotations

import logging
from typing import Any

from services.agents.base import BaseAgent
from services.llm import LLMClient

logger = logging.getLogger(__name__)


class RecruiterAgentError(Exception):
    """Raised when the recruiter agent fails after all retry attempts."""


class RecruiterAgent(BaseAgent):
    """Evaluates a resume from a recruiter's perspective: first-impression
    screening, red-flag detection, and fit scoring against the analyzed JD."""

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
