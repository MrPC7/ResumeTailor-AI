"""ComparisonEngine — deterministic before/after evaluation comparison.

No LLM calls. Pure arithmetic delta computation.
"""
from __future__ import annotations

from schemas.agent_models import ImprovementMetrics, RecruiterEvaluation


class ComparisonEngine:
    """Computes deterministic improvement metrics between two evaluations.

    This is a stateless utility — no LLM, no side effects.
    """

    @staticmethod
    def compare(
        before: RecruiterEvaluation,
        after: RecruiterEvaluation,
    ) -> ImprovementMetrics:
        """Compute improvement deltas between before and after evaluations."""
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


comparison_engine = ComparisonEngine()
