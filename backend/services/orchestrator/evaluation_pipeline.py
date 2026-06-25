"""Pipeline orchestrator — coordinates the v2 multi-agent evaluation workflow."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from schemas.agent_models import CandidateProfile, JobProfile, RecruiterEvaluation
from services.agents.base import Agent

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Raised when the evaluation pipeline fails."""


class PipelineInputError(PipelineError):
    """Raised when pipeline input validation fails."""


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

    Each agent receives the accumulated context from all previous agents.
    """

    def __init__(
        self,
        resume_analyzer: Agent,
        jd_analyzer: Agent,
        recruiter: Agent,
    ) -> None:
        self._resume_analyzer = resume_analyzer
        self._jd_analyzer = jd_analyzer
        self._recruiter = recruiter

    async def run(
        self,
        raw_resume_text: str,
        raw_jd_text: str,
    ) -> EvaluationResult:
        """Execute the full evaluation pipeline.

        Parameters
        ----------
        raw_resume_text:
            Raw text extracted from the candidate's resume.
        raw_jd_text:
            Raw text of the job description.

        Returns
        -------
        EvaluationResult containing candidate_profile, job_profile, and evaluation.

        Raises
        ------
        PipelineInputError:
            If inputs are empty or invalid.
        PipelineError:
            If any agent fails during execution.
        """
        self._validate_inputs(raw_resume_text, raw_jd_text)

        context: dict[str, Any] = {
            "raw_resume_text": raw_resume_text,
            "raw_jd_text": raw_jd_text,
        }

        # Step 1: Extract CandidateProfile
        context = await self._run_agent(self._resume_analyzer, context)

        # Step 2: Extract JobProfile
        context = await self._run_agent(self._jd_analyzer, context)

        # Step 3: Recruiter Evaluation
        context = await self._run_agent(self._recruiter, context)

        return self._build_result(context)

    async def _run_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single agent and merge its output into context."""
        logger.info("Pipeline: running agent '%s'", agent.name)
        try:
            result = await agent.run(context)
            context.update(result)
            return context
        except PipelineError:
            raise
        except Exception as exc:
            raise PipelineError(
                f"Agent '{agent.name}' failed: {exc}"
            ) from exc

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
