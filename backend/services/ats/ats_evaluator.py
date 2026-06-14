"""AI-powered ATS evaluator — orchestrates LLM calls with retry logic."""
from __future__ import annotations

import logging

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse
from services.ats.ats_models import ATSComparisonResult, ATSEvaluationResult
from services.ats.ats_prompt_builder import build_ats_evaluation_prompt
from services.ats.ats_response_parser import ATSParseError, parse_ats_response
from services.resume_extractor.gemini_client import LLMAPIError, LLMClient, LLMParseError

logger = logging.getLogger(__name__)


class ATSEvaluationError(Exception):
    """Raised when ATS evaluation fails after all retries."""


class ATSEvaluator:
    """Reusable ATS evaluation service backed by an LLM client."""

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        self._client = client
        self._max_retries = max(1, max_retries)

    async def evaluate(
        self,
        resume: ExtractResumeResponse,
        jd: AnalyzeJDResponse,
    ) -> ATSEvaluationResult:
        """Evaluate a resume against a JD, retrying on invalid JSON."""
        prompt = build_ats_evaluation_prompt(resume, jd)
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                raw = await self._client.generate_json(prompt)
                return parse_ats_response(raw)
            except (LLMParseError, ATSParseError) as exc:
                logger.warning(
                    "ATS evaluation attempt %d/%d failed (parse): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                last_error = exc
            except LLMAPIError as exc:
                raise ATSEvaluationError(
                    f"LLM API error during ATS evaluation: {exc}"
                ) from exc

        raise ATSEvaluationError(
            f"ATS evaluation failed after {self._max_retries} attempt(s): {last_error}"
        )

    async def compare(
        self,
        original: ExtractResumeResponse,
        customized: ExtractResumeResponse,
        jd: AnalyzeJDResponse,
    ) -> ATSComparisonResult:
        """Evaluate both resumes and compute the improvement delta."""
        try:
            before = await self.evaluate(original, jd)
            after = await self.evaluate(customized, jd)
        except ATSEvaluationError:
            raise
        except Exception as exc:
            raise ATSEvaluationError("ATS comparison failed.") from exc

        return ATSComparisonResult(
            beforeScore=before.overallScore,
            afterScore=after.overallScore,
            improvement=after.overallScore - before.overallScore,
            before=before,
            after=after,
        )
