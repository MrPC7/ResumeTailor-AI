"""ATS scoring configuration.

All weight constants live here so they can be adjusted without touching
business logic.  Weights must sum to 1.0.
"""
from __future__ import annotations

# Contribution of each sub-score to the overall ATS score.
WEIGHT_SKILLS: float = 0.40
WEIGHT_KEYWORDS: float = 0.30
WEIGHT_EXPERIENCE: float = 0.20
WEIGHT_EDUCATION: float = 0.10

# For multi-word skills, how many tokens must overlap before we count a match.
TOKEN_OVERLAP_THRESHOLD: float = 0.75

# Seniority → minimum years of experience expected.
SENIORITY_MIN_YEARS: dict[str, int] = {
    "intern": 0,
    "junior": 1,
    "mid": 3,
    "senior": 5,
    "lead": 7,
    "principal": 8,
    "staff": 8,
    "director": 10,
    "vp": 12,
    "c-level": 15,
}

# Assumed years per experience entry when no date range is parseable.
YEARS_PER_UNLABELLED_EXPERIENCE: float = 1.5

# Keywords that signal education level (used for education scoring).
DEGREE_KEYWORDS: dict[str, int] = {
    "phd": 4,
    "doctorate": 4,
    "master": 3,
    "msc": 3,
    "mba": 3,
    "bachelor": 2,
    "bsc": 2,
    "ba": 2,
    "associate": 1,
    "diploma": 1,
}
