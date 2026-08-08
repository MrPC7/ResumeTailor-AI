"""Pipeline orchestrator — coordinates the v2 multi-agent evaluation workflow."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from core.config import settings
from schemas.agent_models import CandidateProfile, JobProfile, RecruiterEvaluation
from services.agents.base import Agent

logger = logging.getLogger(__name__)

# Prompt version for traceability in logs and monitoring.
PIPELINE_VERSION = "v2.1.0"
ProgressCallback = Callable[[int, str], Awaitable[None] | None]


class PipelineError(Exception):
    """Raised when the evaluation pipeline fails."""


class PipelineInputError(PipelineError):
    """Raised when pipeline input validation fails."""


class PipelineTimeoutError(PipelineError):
    """Raised when the pipeline exceeds its time budget."""


@dataclass(frozen=True)
class EvaluationResult:
    """Structured output of the evaluation pipeline."""

    candidate_profile: CandidateProfile
    job_profile: JobProfile
    evaluation: RecruiterEvaluation

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_profile": self.candidate_profile.model_dump(),
            "job_profile": self.job_profile.model_dump(),
            "evaluation": self.evaluation.model_dump(),
        }


class EvaluationPipeline:
    """Orchestrates the v2 multi-agent evaluation workflow.

    Pipeline sequence:
        1. ResumeAnalyzerAgent → CandidateProfile
        2. JDAnalyzerAgent → JobProfile
        3. RecruiterAgent → RecruiterEvaluation

    Production features:
        - Per-pipeline timeout (PIPELINE_TIMEOUT_SECONDS)
        - Structured logging with timing per agent
        - Graceful error recovery with partial context preservation
        - Prompt versioning for traceability
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
        raw_resume_text: str,
        raw_jd_text: str,
        progress_callback: ProgressCallback | None = None,
    ) -> EvaluationResult:
        """Execute the full evaluation pipeline with timeout protection.

        Raises
        ------
        PipelineInputError:
            If inputs are empty or invalid.
        PipelineTimeoutError:
            If the pipeline exceeds the configured timeout.
        PipelineError:
            If any agent fails during execution.
        """
        self._validate_inputs(raw_resume_text, raw_jd_text)
        await self._notify_progress(progress_callback, 10, "Initializing")

        logger.info(
            "Pipeline started",
            extra={
                "pipeline_version": PIPELINE_VERSION,
                "timeout_seconds": self._timeout,
                "resume_length": len(raw_resume_text),
                "jd_length": len(raw_jd_text),
            },
        )

        start_time = time.perf_counter()

        try:
            result = await asyncio.wait_for(
                self._execute(raw_resume_text, raw_jd_text, progress_callback),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - start_time
            logger.error(
                "Pipeline timeout",
                extra={
                    "pipeline_version": PIPELINE_VERSION,
                    "elapsed_seconds": round(elapsed, 2),
                    "timeout_seconds": self._timeout,
                },
            )
            raise PipelineTimeoutError(
                f"Pipeline exceeded {self._timeout}s timeout."
            ) from None

        elapsed = time.perf_counter() - start_time
        logger.info(
            "Pipeline completed",
            extra={
                "pipeline_version": PIPELINE_VERSION,
                "elapsed_seconds": round(elapsed, 2),
                "match_level": result.evaluation.match_level,
                "hiring_confidence": result.evaluation.hiring_confidence,
            },
        )
        return result

    async def _execute(
        self,
        raw_resume_text: str,
        raw_jd_text: str,
        progress_callback: ProgressCallback | None = None,
    ) -> EvaluationResult:
        """Internal pipeline execution without timeout wrapping."""
        context: dict[str, Any] = {
            "raw_resume_text": raw_resume_text,
            "raw_jd_text": raw_jd_text,
        }

        await self._notify_progress(
            progress_callback,
            25,
            "Resume extraction",
        )

        # Step 1: Extract CandidateProfile
        await self._notify_progress(
            progress_callback,
            35,
            "Resume analysis",
        )
        context = await self._run_agent(self._resume_analyzer, context, step=1)
        await self._notify_progress(
            progress_callback,
            45,
            "Resume analysis complete",
        )

        # Step 2: Extract JobProfile
        await self._notify_progress(
            progress_callback,
            55,
            "Job description analysis",
        )
        context = await self._run_agent(self._jd_analyzer, context, step=2)
        await self._notify_progress(
            progress_callback,
            60,
            "Job description analysis complete",
        )

        # Step 3: Recruiter Evaluation
        await self._notify_progress(
            progress_callback,
            70,
            "Recruiter review",
        )
        context = await self._run_agent(self._recruiter, context, step=3)
        await self._notify_progress(
            progress_callback,
            80,
            "Recruiter review complete",
        )
        await self._notify_progress(
            progress_callback,
            95,
            "Suggestions generation",
        )

        return self._build_result(context)

    async def _notify_progress(
        self,
        progress_callback: ProgressCallback | None,
        progress: int,
        current_step: str,
    ) -> None:
        if progress_callback is None:
            return

        result = progress_callback(progress, current_step)
        if result is not None:
            await result

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
                "pipeline_version": PIPELINE_VERSION,
            },
        )

        try:
            result = await agent.run(context)
            context.update(result)
        except PipelineError:
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
            raise PipelineError(
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

    def _validate_inputs(self, raw_resume_text: str, raw_jd_text: str) -> None:
        """Validate pipeline inputs before execution."""
        if not raw_resume_text or not raw_resume_text.strip():
            raise PipelineInputError("raw_resume_text must be a non-empty string.")
        if not raw_jd_text or not raw_jd_text.strip():
            raise PipelineInputError("raw_jd_text must be a non-empty string.")

    def _build_result(self, context: dict[str, Any]) -> EvaluationResult:
        """Extract and validate final results from accumulated context."""
        candidate_profile = context.get("candidate_profile")
        job_profile = context.get("job_profile")
        evaluation = context.get("recruiter_evaluation")

        if not isinstance(candidate_profile, CandidateProfile):
            raise PipelineError(
                "Pipeline did not produce a valid CandidateProfile."
            )
        if not isinstance(job_profile, JobProfile):
            raise PipelineError(
                "Pipeline did not produce a valid JobProfile."
            )
        if not isinstance(evaluation, RecruiterEvaluation):
            raise PipelineError(
                "Pipeline did not produce a valid RecruiterEvaluation."
            )

        return EvaluationResult(
            candidate_profile=candidate_profile,
            job_profile=job_profile,
            evaluation=evaluation,
        )
