from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Score breakdown
# ---------------------------------------------------------------------------


class ATSScores(BaseModel):
    skills: int = Field(ge=0, le=100)
    keywords: int = Field(ge=0, le=100)
    experience: int = Field(ge=0, le=100)
    education: int = Field(ge=0, le=100)


# ---------------------------------------------------------------------------
# Recommendation groups — each group has a title and selectable items
# ---------------------------------------------------------------------------


class RecommendationGroup(BaseModel):
    title: str
    items: list[str]


# ---------------------------------------------------------------------------
# Full analysis result
# ---------------------------------------------------------------------------


class ATSAnalysisResult(BaseModel):
    overallScore: int = Field(ge=0, le=100)
    scores: ATSScores
    matchedKeywords: list[str]
    missingKeywords: list[str]
    recommendations: list[RecommendationGroup]


# ---------------------------------------------------------------------------
# Before-vs-after comparison
# ---------------------------------------------------------------------------


class ATSComparisonResult(BaseModel):
    beforeScore: int = Field(ge=0, le=100)
    afterScore: int = Field(ge=0, le=100)
    improvement: int
    before: ATSAnalysisResult
    after: ATSAnalysisResult
