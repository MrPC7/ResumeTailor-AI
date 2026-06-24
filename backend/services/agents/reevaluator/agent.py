"""Reevaluator agent — re-scores tailored resume to verify improvement."""
from __future__ import annotations

import logging
from typing import Any

from services.agents.base import BaseAgent
from services.llm import LLMClient

logger = logging.getLogger(__name__)


class ReevaluatorAgentError(Exception):
    """Raised when the reevaluator agent fails after all retry attempts."""


class ReevaluatorAgent(BaseAgent):
    """Re-evaluates a tailored resume against the original JD to confirm
    that the changes made by the tailor agent actually improved the score."""

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
