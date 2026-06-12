from __future__ import annotations

from schemas.gap_analysis import GapAnalysisRequest, GapAnalysisResponse
from services.gap_analyzer.gap_engine import compute_gap


class GapAnalysisError(Exception):
    pass


class GapAnalyzer:
    @staticmethod
    def compute(payload: GapAnalysisRequest) -> GapAnalysisResponse:
        try:
            matched, missing, recommendations = compute_gap(
                resume=payload.resume,
                jd=payload.jd,
            )
        except Exception as exc:
            raise GapAnalysisError("Failed to compute gap analysis.") from exc

        return GapAnalysisResponse(
            matchedSkills=matched,
            missingSkills=missing,
            recommendations=recommendations,
        )
