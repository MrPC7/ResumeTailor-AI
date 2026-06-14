"""Pydantic models for AI-powered ATS evaluation."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ATSScores(BaseModel):
    skills: int = Field(ge=0, le=100)
    keywords: int = Field(ge=0, le=100)
    experience: int = Field(ge=0, le=100)
    education: int = Field(ge=0, le=100)
    overallFit: int = Field(ge=0, le=100, alias="overallFit")


class ATSEvaluationResult(BaseModel):
    overallScore: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    scores: ATSScores
    strengths: list[str]
    weaknesses: list[str]
    missingKeywords: list[str]
    recommendedActions: list[str]


class ATSComparisonResult(BaseModel):
    beforeScore: int = Field(ge=0, le=100)
    afterScore: int = Field(ge=0, le=100)
    improvement: int
    before: ATSEvaluationResult
    after: ATSEvaluationResult


class PotentialScoreResult(BaseModel):
    currentScore: int = Field(ge=0, le=100)
    potentialScore: int = Field(ge=0, le=100)
    improvementPotential: int = Field(ge=0)


# ---------------------------------------------------------------------------
# Recommendation Intelligence
# ---------------------------------------------------------------------------

class ImpactLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Recommendation(BaseModel):
    id: str
    title: str
    description: str
    impactLevel: Literal["critical", "high", "medium", "low"]
    estimatedPoints: int = Field(ge=0, le=20)


class RecommendationGroup(BaseModel):
    groupId: str
    groupTitle: str
    recommendations: list[Recommendation]


class RecommendationReport(BaseModel):
    totalEstimatedGain: int = Field(ge=0)
    groups: list[RecommendationGroup]
