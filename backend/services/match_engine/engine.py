from __future__ import annotations

from schemas.match_score import MatchScoreRequest, MatchScoreResponse
from services.match_engine.scoring import calculate_match_scores


class MatchEngineError(Exception):
    pass


class MatchEngine:
    @staticmethod
    def compute(payload: MatchScoreRequest) -> MatchScoreResponse:
        try:
            score, skill_score, keyword_score, experience_score = calculate_match_scores(
                resume=payload.resume,
                jd=payload.jd,
            )
        except Exception as exc:
            raise MatchEngineError("Failed to calculate match score.") from exc

        return MatchScoreResponse(
            score=score,
            skillScore=skill_score,
            keywordScore=keyword_score,
            experienceScore=experience_score,
        )
