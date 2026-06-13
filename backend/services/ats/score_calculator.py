"""Deterministic weighted scoring engine for ATS analysis."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse
from services.ats.config import (
    DEGREE_KEYWORDS,
    SENIORITY_MIN_YEARS,
    TOKEN_OVERLAP_THRESHOLD,
    WEIGHT_EDUCATION,
    WEIGHT_EXPERIENCE,
    WEIGHT_KEYWORDS,
    WEIGHT_SKILLS,
    YEARS_PER_UNLABELLED_EXPERIENCE,
)
from services.ats.keyword_matcher import (
    build_resume_term_set,
    keyword_matches,
    normalize,
    split_matched_missing,
)


def _current_year() -> int:
    return datetime.now(tz=timezone.utc).year


def _clamp(value: float) -> int:
    return max(0, min(100, int(round(value))))


# ---------------------------------------------------------------------------
# Skills score
# ---------------------------------------------------------------------------


def compute_skills_score(
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
    full_phrases: set[str],
    token_pool: set[str],
) -> int:
    required = [s for s in jd.requiredSkills if s.strip()]
    preferred = [s for s in jd.preferredSkills if s.strip()]
    if not required and not preferred:
        return 75  # neutral: no data to compare against

    def _pct(skills: list[str]) -> float:
        if not skills:
            return 100.0
        hits = sum(
            1
            for s in skills
            if keyword_matches(s, full_phrases, token_pool, TOKEN_OVERLAP_THRESHOLD)
        )
        return (hits / len(skills)) * 100.0

    req_pct = _pct(required)
    pref_pct = _pct(preferred)

    # Required skills weigh 80%; preferred 20%
    if required and preferred:
        return _clamp(req_pct * 0.8 + pref_pct * 0.2)
    if required:
        return _clamp(req_pct)
    return _clamp(pref_pct)


# ---------------------------------------------------------------------------
# Keyword score
# ---------------------------------------------------------------------------


def compute_keyword_score(
    jd: AnalyzeJDResponse,
    full_phrases: set[str],
    token_pool: set[str],
) -> int:
    keywords = [k for k in jd.atsKeywords if k.strip()]
    if not keywords:
        return 75
    hits = sum(
        1
        for k in keywords
        if keyword_matches(k, full_phrases, token_pool, TOKEN_OVERLAP_THRESHOLD)
    )
    return _clamp((hits / len(keywords)) * 100.0)


# ---------------------------------------------------------------------------
# Experience score
# ---------------------------------------------------------------------------


def _extract_years(duration: str) -> list[int]:
    values = [int(v) for v in re.findall(r"\b(19\d{2}|20\d{2})\b", duration)]
    return [y for y in values if 1950 <= y <= _current_year() + 1]


def _estimate_years(resume: ExtractResumeResponse) -> float:
    all_years: list[int] = []
    for item in resume.experience:
        all_years.extend(_extract_years(item.duration))
    if all_years:
        return float(max(all_years) - min(all_years) + 1)
    return float(len(resume.experience)) * YEARS_PER_UNLABELLED_EXPERIENCE


def compute_experience_score(resume: ExtractResumeResponse, jd: AnalyzeJDResponse) -> int:
    seniority = normalize(jd.seniority or "")
    required_years = SENIORITY_MIN_YEARS.get(seniority)
    if required_years is None:
        return 60  # neutral
    if required_years == 0:
        return 100
    return _clamp((_estimate_years(resume) / required_years) * 100.0)


# ---------------------------------------------------------------------------
# Education score
# ---------------------------------------------------------------------------


def compute_education_score(resume: ExtractResumeResponse) -> int:
    if not resume.education:
        return 50  # penalise missing education, but not zero

    best = 0
    for edu in resume.education:
        text = normalize(f"{edu.degree} {edu.institution}")
        for keyword, level in DEGREE_KEYWORDS.items():
            if keyword in text:
                best = max(best, level)

    if best == 0:
        return 60  # degree listed but unrecognised → small neutral bonus
    # Scale: 1 → 70, 2 → 80, 3 → 90, 4 → 100
    return min(100, 60 + best * 10)


# ---------------------------------------------------------------------------
# Overall
# ---------------------------------------------------------------------------


def compute_overall_score(skills: int, keywords: int, experience: int, education: int) -> int:
    return _clamp(
        skills * WEIGHT_SKILLS
        + keywords * WEIGHT_KEYWORDS
        + experience * WEIGHT_EXPERIENCE
        + education * WEIGHT_EDUCATION
    )


# ---------------------------------------------------------------------------
# Keyword split helper (re-exported for ATS engine)
# ---------------------------------------------------------------------------


def build_keyword_split(
    jd: AnalyzeJDResponse,
    full_phrases: set[str],
    token_pool: set[str],
) -> tuple[list[str], list[str]]:
    """Return (matched_keywords, missing_keywords) from JD atsKeywords."""
    all_kws = list(dict.fromkeys(kw for kw in jd.atsKeywords if kw.strip()))
    return split_matched_missing(all_kws, full_phrases, token_pool, TOKEN_OVERLAP_THRESHOLD)
