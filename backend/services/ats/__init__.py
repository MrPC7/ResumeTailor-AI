from __future__ import annotations

from core.config import settings
from services.ats.ats_evaluator import ATSEvaluator
from services.llm import llm_client

ats_evaluator = ATSEvaluator(
    client=llm_client,
    max_retries=settings.GEMINI_MAX_RETRIES,
)

__all__ = ["ats_evaluator"]
