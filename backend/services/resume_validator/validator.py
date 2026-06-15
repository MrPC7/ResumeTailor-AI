"""Resume validation service — 3-layer verification pipeline.

Layer 1: File validation (handled upstream by parse_resume_service).
Layer 2: Structure-based confidence scoring from extracted resume data.
Layer 3: AI verification via LLM for uncertain cases.
"""
from __future__ import annotations

import logging
import re

from schemas.extract_resume import StructuredResume

logger = logging.getLogger(__name__)

# Confidence thresholds
_HIGH_CONFIDENCE_THRESHOLD = 70   # Accept without AI check
_LOW_CONFIDENCE_THRESHOLD = 30    # Reject without AI check
# Between 30–70 → AI verification


def compute_resume_confidence(resume: StructuredResume) -> int:
    """Score 0-100 based on presence of common resume sections."""
    score = 0

    # Identity fields (max 20)
    if resume.name and len(resume.name.strip()) >= 2:
        score += 8
    if resume.email and re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", resume.email):
        score += 7
    if resume.phone and re.search(r"\d{3,}", re.sub(r"[\s\-().+]", "", resume.phone)):
        score += 5

    # Skills (max 20)
    skill_count = len(resume.skills)
    if skill_count >= 5:
        score += 20
    elif skill_count >= 3:
        score += 15
    elif skill_count >= 1:
        score += 8

    # Experience (max 25)
    exp_count = len(resume.experience)
    if exp_count >= 2:
        score += 25
    elif exp_count == 1:
        score += 15

    # Education (max 15)
    edu_count = len(resume.education)
    if edu_count >= 1:
        score += 15

    # Projects (max 10)
    if len(resume.projects) >= 1:
        score += 10

    # Summary / objective (max 10)
    if resume.summary and len(resume.summary.strip()) >= 20:
        score += 10

    return min(score, 100)


def needs_ai_verification(confidence: int) -> bool:
    """Return True if confidence falls in the uncertain range."""
    return _LOW_CONFIDENCE_THRESHOLD <= confidence < _HIGH_CONFIDENCE_THRESHOLD
