"""AI-powered resume verification for uncertain cases."""
from __future__ import annotations

import json
import logging

from services.llm import LLMClient, LLMAPIError, LLMParseError

logger = logging.getLogger(__name__)

_VERIFY_PROMPT = """\
You are a document classifier. Determine whether the following text is a professional resume / CV.

A professional resume typically contains:
- A person's name and contact information
- Work experience or employment history
- Education background
- Skills or competencies
- Possibly a summary/objective, projects, or certifications

The text may also be a bank statement, invoice, letter, academic paper, random document, or any other non-resume content.

Analyze the text below and return ONLY a valid JSON object:
{{
  "isResume": true or false,
  "confidence": <int 0-100>,
  "reason": "Brief explanation of your determination"
}}

Document text (first 3000 chars):
{document_text}"""


class AIResumeVerifier:
    """Uses an LLM to verify whether a document is a resume."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    async def verify(self, raw_text: str) -> dict:
        """Return {"isResume": bool, "confidence": int, "reason": str}."""
        truncated = raw_text[:3000]
        prompt = _VERIFY_PROMPT.format(document_text=truncated)

        try:
            result = await self._client.generate_json(prompt)
            is_resume = bool(result.get("isResume", False))
            confidence = int(result.get("confidence", 0))
            reason = str(result.get("reason", ""))
            return {
                "isResume": is_resume,
                "confidence": max(0, min(100, confidence)),
                "reason": reason,
            }
        except (LLMAPIError, LLMParseError) as exc:
            logger.warning("AI resume verification failed: %s", exc)
            # On AI failure, be permissive — don't block the user
            return {
                "isResume": True,
                "confidence": 50,
                "reason": "AI verification unavailable; allowing upload.",
            }
