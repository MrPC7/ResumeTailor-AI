"""Re-evaluation pipeline — evaluates original and optimized resumes against a JD."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from core.config import settings
from schemas.agent_models import (
    ImprovementMetrics,
    JobProfile,
    RecruiterEvaluation,
)
from services.agents.base import Agent

logger = logging.getLogger(__name__)

REEVALUATION_PIPELINE_VERSION = "v1.0.0"


class ReevaluationPipelineError(Exception):
    """Raised when the re-evaluation pipeline fails."""


class ReevaluationInputError(ReevaluationPipelineError):
    """Raised when pipeline input validation fails."""


class ReevaluationTimeoutError(ReevaluationPipelineError):
    """Raised when the pipeline exceeds its time budget."""


@dataclass(frozen=True)
class ReevaluationResult:
    """Structured output of the re-evaluation pipeline."""

    before: RecruiterEvaluation
    after: RecruiterEvaluation
    improvement: ImprovementMetrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "before": self.before.model_dump(),
            "after": self.after.model_dump(),
            "improvement": self.improvement.model_dump(),
        }


class ReevaluationPipeline:
    """Orchestrates re-evaluation of original vs optimized resumes.

    Pipeline sequence:
        1. ResumeAnalyzerAgent(original) → CandidateProfile
        2. JDAnalyzerAgent → JobProfile
        3. RecruiterAgent(original profile, job) → before evaluation
        4. ResumeAnalyzerAgent(optimized) → CandidateProfile
        5. RecruiterAgent(optimized profile, job) → after evaluation
        6. Compute deterministic improvement metrics
    """

    def __init__(
        self,
        resume_analyzer: Agent,
        jd_analyzer: Agent,
        recruiter: Agent,
        timeout_seconds: int | None = None,
    ) -> None:
        self._resume_analyzer = resume_analyzer
        self._jd_analyzer = jd_analyzer
        self._recruiter = recruiter
        self._timeout = timeout_seconds or settings.PIPELINE_TIMEOUT_SECONDS

    async def run(
        self,
        original_resume_text: str,
        optimized_resume_text: str,
        raw_jd_text: str,
    ) -> ReevaluationResult:
        """Execute the full re-evaluation pipeline with timeout protection."""
        self._validate_inputs(original_resume_text, optimized_resume_text, raw_jd_text)

        logger.info(
            "Reevaluation pipeline started",
            extra={
                "pipeline_version": REEVALUATION_PIPELINE_VERSION,
                "timeout_seconds": self._timeout,
                "original_length": len(original_resume_text),
                "optimized_length": len(optimized_resume_text),
                "jd_length": len(raw_jd_text),
            },
        )

        start_time = time.perf_counter()

        try:
            result = await asyncio.wait_for(
                self._execute(original_resume_text, optimized_resume_text, raw_jd_text),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - start_time
            logger.error(
                "Reevaluation pipeline timeout",
                extra={
                    "pipeline_version": REEVALUATION_PIPELINE_VERSION,
                    "elapsed_seconds": round(elapsed, 2),
                    "timeout_seconds": self._timeout,
                },
            )
            raise ReevaluationTimeoutError(
                f"Pipeline exceeded {self._timeout}s timeout."
            ) from None

        elapsed = time.perf_counter() - start_time
        logger.info(
            "Reevaluation pipeline completed",
            extra={
                "pipeline_version": REEVALUATION_PIPELINE_VERSION,
                "elapsed_seconds": round(elapsed, 2),
                "hiring_confidence_delta": result.improvement.hiring_confidence_delta,
                "improved": result.improvement.improved,
            },
        )
        return result

    async def _execute(
        self,
        original_resume_text: str,
        optimized_resume_text: str,
        raw_jd_text: str,
    ) -> ReevaluationResult:
        """Internal pipeline execution without timeout wrapping."""
        # Step 1: Analyze original resume
        original_ctx: dict[str, Any] = {"raw_resume_text": original_resume_text}
        original_ctx = await self._run_agent(self._resume_analyzer, original_ctx, step=1)

        # Step 2: Analyze job description
        jd_ctx: dict[str, Any] = {"raw_jd_text": raw_jd_text}
        jd_ctx = await self._run_agent(self._jd_analyzer, jd_ctx, step=2)

        job_profile: JobProfile = jd_ctx["job_profile"]

        # Step 3: Recruiter evaluation on original
        before_ctx: dict[str, Any] = {
            "candidate_profile": original_ctx["candidate_profile"],
            "job_profile": job_profile,
        }
        before_ctx = await self._run_agent(self._recruiter, before_ctx, step=3)
        before_eval: RecruiterEvaluation = before_ctx["recruiter_evaluation"]

        # Step 4: Analyze optimized resume
        optimized_ctx: dict[str, Any] = {"raw_resume_text": optimized_resume_text}
        optimized_ctx = await self._run_agent(self._resume_analyzer, optimized_ctx, step=4)

        # Step 5: Recruiter evaluation on optimized
        after_ctx: dict[str, Any] = {
            "candidate_profile": optimized_ctx["candidate_profile"],
            "job_profile": job_profile,
        }
        after_ctx = await self._run_agent(self._recruiter, after_ctx, step=5)
        after_eval: RecruiterEvaluation = after_ctx["recruiter_evaluation"]

        # Step 6: Compute improvement metrics
        improvement = self._compute_improvement(before_eval, after_eval)

        return ReevaluationResult(
            before=before_eval,
            after=after_eval,
            improvement=improvement,
        )

    async def _run_agent(
        self, agent: Agent, context: dict[str, Any], step: int
    ) -> dict[str, Any]:
        """Execute a single agent with structured logging."""
        agent_start = time.perf_counter()
        logger.info(
            "Agent started",
            extra={
                "agent": agent.name,
                "step": step,
                "pipeline_version": REEVALUATION_PIPELINE_VERSION,
            },
        )

        try:
            result = await agent.run(context)
            context.update(result)
        except ReevaluationPipelineError:
            raise
        except Exception as exc:
            elapsed = time.perf_counter() - agent_start
            logger.error(
                "Agent failed",
                extra={
                    "agent": agent.name,
                    "step": step,
                    "elapsed_seconds": round(elapsed, 2),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            raise ReevaluationPipelineError(
                f"Agent '{agent.name}' failed: {exc}"
            ) from exc

        elapsed = time.perf_counter() - agent_start
        logger.info(
            "Agent completed",
            extra={
                "agent": agent.name,
                "step": step,
                "elapsed_seconds": round(elapsed, 2),
            },
        )
        return context

    def _validate_inputs(
        self,
        original_resume_text: str,
        optimized_resume_text: str,
        raw_jd_text: str,
    ) -> None:
        """Validate pipeline inputs before execution."""
        if not original_resume_text or not original_resume_text.strip():
            raise ReevaluationInputError(
                "original_resume_text must be a non-empty string."
            )
        if not optimized_resume_text or not optimized_resume_text.strip():
            raise ReevaluationInputError(
                "optimized_resume_text must be a non-empty string."
            )
        if not raw_jd_text or not raw_jd_text.strip():
            raise ReevaluationInputError(
                "raw_jd_text must be a non-empty string."
            )

    def _compute_improvement(
        self,
        before: RecruiterEvaluation,
        after: RecruiterEvaluation,
    ) -> ImprovementMetrics:
        """Deterministic calculation of improvement deltas."""
        return ImprovementMetrics(
            hiring_confidence_delta=after.hiring_confidence - before.hiring_confidence,
            interview_probability_delta=after.interview_probability - before.interview_probability,
            gaps_before=len(before.gaps),
            gaps_after=len(after.gaps),
            gaps_reduced=len(before.gaps) - len(after.gaps),
            strengths_before=len(before.strengths),
            strengths_after=len(after.strengths),
            strengths_gained=len(after.strengths) - len(before.strengths),
            match_level_before=before.match_level,
            match_level_after=after.match_level,
            improved=after.hiring_confidence > before.hiring_confidence,
        )
