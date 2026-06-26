"""Reevaluator agent — runs recruiter evaluation twice and computes improvement."""
from __future__ import annotations

import logging
from typing import Any

from schemas.agent_models import (
    CandidateProfile,
    ImprovementMetrics,
    JobProfile,
    RecruiterEvaluation,
    ReevaluationResult,
    TailoredResume,
    Skill,
    WorkExperience,
    Project,
)
from services.agents.base import BaseAgent
from services.agents.recruiter.agent import RecruiterAgent
from services.llm import LLMClient

logger = logging.getLogger(__name__)


class ReevaluatorAgentError(Exception):
    """Raised when the reevaluator agent fails."""


class ReevaluatorAgent(BaseAgent):
    """Re-evaluates original and tailored resumes against the JD using
    the RecruiterAgent, then computes deterministic improvement deltas.

    This agent does NOT call the LLM directly — it delegates to a
    RecruiterAgent instance for both evaluations.
    """

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        super().__init__(client=client, max_retries=max_retries)
        self._recruiter = RecruiterAgent(client=client, max_retries=max_retries)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run reevaluation using pipeline context.

        Parameters
        ----------
        context:
            Must contain:
            - 'candidate_profile' (CandidateProfile) — original resume
            - 'job_profile' (JobProfile)
            - 'tailored_resume' (TailoredResume) — optimized resume
            - 'recruiter_evaluation' (RecruiterEvaluation) — original "before" eval

        Returns
        -------
        dict with 'reevaluation_result' (ReevaluationResult instance).
        """
        candidate: CandidateProfile = context["candidate_profile"]
        job: JobProfile = context["job_profile"]
        tailored: TailoredResume = context["tailored_resume"]
        before_eval: RecruiterEvaluation = context["recruiter_evaluation"]

        result = await self.reevaluate(candidate, job, tailored, before_eval)
        return {"reevaluation_result": result}

    async def reevaluate(
        self,
        original_profile: CandidateProfile,
        job: JobProfile,
        tailored: TailoredResume,
        before_eval: RecruiterEvaluation,
    ) -> ReevaluationResult:
        """Evaluate tailored resume and compute improvement metrics.

        Parameters
        ----------
        original_profile:
            The original CandidateProfile (before tailoring).
        job:
            The target JobProfile.
        tailored:
            The TailoredResume output from ResumeTailorAgent.
        before_eval:
            The original RecruiterEvaluation (already computed).

        Returns
        -------
        ReevaluationResult with before, after, and improvement metrics.
        """
        # Build a CandidateProfile from the tailored resume for "after" evaluation
        tailored_profile = self._build_tailored_profile(original_profile, tailored)

        # Run recruiter evaluation on the tailored profile
        try:
            after_eval = await self._recruiter.evaluate(tailored_profile, job)
        except Exception as exc:
            raise ReevaluatorAgentError(
                f"Failed to evaluate tailored resume: {exc}"
            ) from exc

        # Compute deterministic improvement metrics
        improvement = self._compute_improvement(before_eval, after_eval)

        return ReevaluationResult(
            before=before_eval,
            after=after_eval,
            improvement=improvement,
        )

    def _build_tailored_profile(
        self,
        original: CandidateProfile,
        tailored: TailoredResume,
    ) -> CandidateProfile:
        """Convert TailoredResume back into a CandidateProfile for evaluation."""
        return CandidateProfile(
            skills=[
                Skill(name=s, category="")
                for s in tailored.skills
            ],
            work_experience=[
                WorkExperience(
                    company=exp.company,
                    position=exp.position,
                    duration=exp.duration,
                    responsibilities=[exp.description] if exp.description else [],
                    technologies=exp.technologies,
                )
                for exp in tailored.experience
            ],
            education=original.education,
            projects=[
                Project(
                    name=proj.name,
                    description=proj.description,
                    technologies=proj.technologies,
                    role="",
                )
                for proj in tailored.projects
            ],
            certifications=original.certifications,
            total_years_experience=original.total_years_experience,
            primary_domain=original.primary_domain,
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
