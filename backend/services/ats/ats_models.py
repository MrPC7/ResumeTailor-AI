"""Pydantic models for AI-powered ATS evaluation."""
from __future__ import annotations

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
