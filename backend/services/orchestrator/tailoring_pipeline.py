"""Tailoring pipeline — orchestrates suggestion-driven resume rewriting."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from core.config import settings
from schemas.agent_models import (
    CandidateProfile,
    JobProfile,
    RecruiterEvaluation,
    Suggestion,
    TailoredResume,
)
from services.agents.resume_tailor.agent import ResumeTailorAgent, ResumeTailorAgentError

logger = logging.getLogger(__name__)

TAILORING_PIPELINE_VERSION = "v2.1.0"

# Length constraints — single A4 page budget
A4_CHAR_BUDGET = 3200
LENGTH_OVERFLOW_THRESHOLD = 0.20  # 20% max increase over original


class TailoringPipelineError(Exception):
    """Raised when the tailoring pipeline fails."""


class TailoringValidationError(TailoringPipelineError):
    """Raised when input validation fails."""


class TailoringTimeoutError(TailoringPipelineError):
    """Raised when the tailoring pipeline exceeds its time budget."""


@dataclass(frozen=True)
class TailoringResult:
    """Output of the tailoring pipeline."""

    tailored_resume: TailoredResume
    original_length: int
    tailored_length: int
    length_within_budget: bool
    suggestions_applied: int
    success: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tailored_resume": self.tailored_resume.model_dump(),
            "original_length": self.original_length,
            "tailored_length": self.tailored_length,
            "length_within_budget": self.length_within_budget,
            "suggestions_applied": self.suggestions_applied,
            "success": self.success,
            "error": self.error,
        }


@dataclass(frozen=True)
class TailoringFailureResult:
    """Returned when tailoring fails — contains original resume + error."""

    original_resume: CandidateProfile
    success: bool = False
    error: str = ""
    error_type: str = ""
    suggestions_attempted: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_resume": self.original_resume.model_dump(),
            "success": self.success,
            "error": self.error,
            "error_type": self.error_type,
            "suggestions_attempted": self.suggestions_attempted,
        }


class TailoringPipeline:
    """Orchestrates the suggestion-driven resume tailoring workflow.

    Pipeline:
        1. Validate suggestions (non-empty, well-formed)
        2. Resume Tailor Agent (apply selected suggestions)
        3. Length Guard (check A4 constraints)
        4. Resume Validation (structural integrity)
        5. Return optimized resume OR original with error

    Transactional: if any step fails, returns original resume with detailed error.
    """

    def __init__(
        self,
        tailor_agent: ResumeTailorAgent,
        timeout_seconds: int | None = None,
    ) -> None:
        self._tailor = tailor_agent
        self._timeout = timeout_seconds or settings.PIPELINE_TIMEOUT_SECONDS

    async def run(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        evaluation: RecruiterEvaluation,
        selected_suggestions: list[Suggestion],
        all_suggestions: list[Suggestion] | None = None,
    ) -> TailoringResult | TailoringFailureResult:
        """Execute the tailoring pipeline with transactional semantics.

        On success: returns TailoringResult with tailored resume.
        On failure: returns TailoringFailureResult with original resume + error.
        """
        logger.info(
            "Tailoring pipeline started",
            extra={
                "pipeline_version": TAILORING_PIPELINE_VERSION,
                "suggestions_count": len(selected_suggestions),
                "timeout_seconds": self._timeout,
            },
        )

        start_time = time.perf_counter()

        # Step 1: Validate suggestions
        validation_error = self._validate_suggestions(selected_suggestions)
        if validation_error:
            return TailoringFailureResult(
                original_resume=candidate,
                error=validation_error,
                error_type="validation",
                suggestions_attempted=len(selected_suggestions),
            )

        # Step 2-4: Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._execute(
                    candidate, job, evaluation,
                    selected_suggestions, all_suggestions,
                ),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - start_time
            logger.error(
                "Tailoring pipeline timeout",
                extra={
                    "elapsed_seconds": round(elapsed, 2),
                    "timeout_seconds": self._timeout,
                },
            )
            return TailoringFailureResult(
                original_resume=candidate,
                error=f"Tailoring timed out after {self._timeout}s.",
                error_type="timeout",
                suggestions_attempted=len(selected_suggestions),
            )
        except ResumeTailorAgentError as exc:
            elapsed = time.perf_counter() - start_time
            logger.error(
                "Tailoring agent failed",
                extra={
                    "elapsed_seconds": round(elapsed, 2),
                    "error": str(exc),
                },
            )
            return TailoringFailureResult(
                original_resume=candidate,
                error=f"Resume tailoring failed: {exc}",
                error_type="agent_error",
                suggestions_attempted=len(selected_suggestions),
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            logger.error(
                "Tailoring pipeline unexpected error",
                extra={
                    "elapsed_seconds": round(elapsed, 2),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            return TailoringFailureResult(
                original_resume=candidate,
                error=f"Unexpected error: {exc}",
                error_type="unexpected",
                suggestions_attempted=len(selected_suggestions),
            )

        elapsed = time.perf_counter() - start_time
        logger.info(
            "Tailoring pipeline completed",
            extra={
                "pipeline_version": TAILORING_PIPELINE_VERSION,
                "elapsed_seconds": round(elapsed, 2),
                "success": result.success,
                "suggestions_applied": result.suggestions_applied,
                "length_within_budget": result.length_within_budget,
            },
        )
        return result

    async def _execute(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        evaluation: RecruiterEvaluation,
        selected_suggestions: list[Suggestion],
        all_suggestions: list[Suggestion] | None,
    ) -> TailoringResult:
        """Internal execution without timeout wrapping."""
        unselected = []
        if all_suggestions:
            selected_ids = {s.id for s in selected_suggestions}
            unselected = [s for s in all_suggestions if s.id not in selected_ids]

        # Step 2: Resume Tailor Agent
        tailored = await self._tailor.tailor(
            candidate, job, evaluation,
            selected_suggestions, unselected,
        )

        # Step 3: Length Guard
        original_length = self._measure_length(candidate)
        tailored_length = self._measure_tailored_length(tailored)
        length_ok = self._check_length(original_length, tailored_length)

        # Step 4: Resume Validation
        validation_issues = self._validate_tailored(tailored, candidate)
        if validation_issues:
            logger.warning(
                "Tailored resume validation issues (non-blocking)",
                extra={"issues": validation_issues},
            )

        return TailoringResult(
            tailored_resume=tailored,
            original_length=original_length,
            tailored_length=tailored_length,
            length_within_budget=length_ok,
            suggestions_applied=len(tailored.improvements_made),
            success=True,
        )

    def _validate_suggestions(self, suggestions: list[Suggestion]) -> str | None:
        """Validate suggestions before processing. Returns error message or None."""
        if not suggestions:
            return "No suggestions selected. At least one suggestion is required."
        for s in suggestions:
            if not s.id or not s.id.strip():
                return f"Suggestion missing id: {s.title or 'unknown'}"
            if not s.title or not s.title.strip():
                return f"Suggestion {s.id} missing title."
        return None

    def _measure_length(self, profile: CandidateProfile) -> int:
        """Measure approximate character length of original profile."""
        total = 0
        total += sum(len(s.name) for s in profile.skills)
        for exp in profile.work_experience:
            total += len(exp.company) + len(exp.position) + len(exp.duration)
            total += sum(len(r) for r in exp.responsibilities)
        for proj in profile.projects:
            total += len(proj.name) + len(proj.description)
        return total

    def _measure_tailored_length(self, tailored: TailoredResume) -> int:
        """Measure approximate character length of tailored resume."""
        total = len(tailored.summary)
        total += sum(len(s) for s in tailored.skills)
        for exp in tailored.experience:
            total += len(exp.company) + len(exp.position) + len(exp.duration)
            total += len(exp.description)
        for proj in tailored.projects:
            total += len(proj.name) + len(proj.description)
        return total

    def _check_length(self, original: int, tailored: int) -> bool:
        """Check if tailored resume is within acceptable length increase."""
        if original == 0:
            return tailored <= A4_CHAR_BUDGET
        increase = (tailored - original) / original if original > 0 else 0
        return increase <= LENGTH_OVERFLOW_THRESHOLD and tailored <= A4_CHAR_BUDGET

    def _validate_tailored(
        self, tailored: TailoredResume, original: CandidateProfile
    ) -> list[str]:
        """Validate structural integrity of tailored resume. Returns issues list."""
        issues: list[str] = []

        # Check experience count preserved
        if len(tailored.experience) != len(original.work_experience):
            issues.append(
                f"Experience count mismatch: original={len(original.work_experience)}, "
                f"tailored={len(tailored.experience)}"
            )

        # Check project count preserved
        if len(tailored.projects) != len(original.projects):
            issues.append(
                f"Project count mismatch: original={len(original.projects)}, "
                f"tailored={len(tailored.projects)}"
            )

        # Check identity preservation (company names must match)
        for i, (orig, tail) in enumerate(
            zip(original.work_experience, tailored.experience)
        ):
            if orig.company and tail.company and orig.company != tail.company:
                issues.append(
                    f"Experience[{i}] company changed: '{orig.company}' → '{tail.company}'"
                )

        # Check no new skills added
        original_skills = {s.name.lower() for s in original.skills}
        for skill in tailored.skills:
            if skill.lower() not in original_skills:
                issues.append(f"New skill added that wasn't in original: '{skill}'")

        return issues
