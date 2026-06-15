"""ATS Potential Score Prediction Engine.

Estimates the maximum realistic ATS score a candidate could achieve
by addressing identified gaps — without promising impossible scores.

The prediction is deterministic (no LLM call) and based purely on the
current evaluation data, resume structure, and JD requirements.
"""
from __future__ import annotations

import re

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse
from schemas.ats_models import ATSEvaluationResult, PotentialScoreResult


# ---------------------------------------------------------------------------
# Seniority gap ceiling — a fresher can never reach 95+ for a Staff role.
# Maps (resume seniority bucket, JD seniority bucket) → hard ceiling.
# ---------------------------------------------------------------------------

_SENIORITY_ORDER = [
    "intern", "junior", "mid", "senior", "lead",
    "principal", "staff", "director", "vp", "c-level",
]

_SENIORITY_CEILINGS: dict[int, int] = {
    # gap_levels → max possible overall score
    0: 98,   # same level
    1: 94,   # one level below
    2: 88,   # two levels below
    3: 82,   # three levels below
    4: 75,   # four+ levels below
}


def _seniority_index(label: str | None) -> int:
    """Return seniority rank (0=intern … 9=c-level), default 2 (mid)."""
    if not label:
        return 2
    cleaned = re.sub(r"[^a-z]", "", label.strip().lower())
    for i, lvl in enumerate(_SENIORITY_ORDER):
        if lvl in cleaned:
            return i
    return 2  # unknown → assume mid


def _estimate_resume_seniority(resume: ExtractResumeResponse) -> int:
    """Heuristic: guess candidate seniority from experience count + years."""
    exp_count = len(resume.experience)
    # Try to extract year spans
    all_years: list[int] = []
    for item in resume.experience:
        all_years.extend(
            int(v) for v in re.findall(r"\b(19\d{2}|20\d{2})\b", item.duration)
            if 1950 <= int(v) <= 2030
        )
    total_years = float(max(all_years) - min(all_years) + 1) if len(all_years) >= 2 else exp_count * 1.5

    if total_years >= 12:
        return 7   # director-ish
    if total_years >= 8:
        return 5   # principal/staff
    if total_years >= 5:
        return 3   # senior
    if total_years >= 2:
        return 2   # mid
    if total_years >= 1:
        return 1   # junior
    return 0       # intern / fresher


def _clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(round(value))))


# ---------------------------------------------------------------------------
# Per-dimension potential estimators
# ---------------------------------------------------------------------------

def _potential_skills(current: int, missing_required: int, missing_preferred: int) -> int:
    """Estimate how high skills score could go if gaps are addressed."""
    # Each missing required skill recovered adds ~3–5 pts (diminishing)
    recoverable = min(missing_required, 8) * 4.0 + min(missing_preferred, 5) * 1.5
    return _clamp(current + recoverable)


def _potential_keywords(current: int, missing_keyword_count: int) -> int:
    """Each missing keyword recovered adds ~2–3 pts."""
    recoverable = min(missing_keyword_count, 15) * 2.5
    return _clamp(current + recoverable)


def _potential_experience(
    current: int,
    has_metrics: bool,
    has_weak_verbs: bool,
    bullet_count: int,
) -> int:
    """Estimate experience score uplift from better bullets."""
    uplift = 0.0
    if not has_metrics:
        uplift += 8.0   # adding quantifiable metrics
    if has_weak_verbs:
        uplift += 5.0   # replacing weak verbs with action verbs
    if bullet_count < 3:
        uplift += 4.0   # adding more experience entries
    return _clamp(current + uplift)


def _potential_education(current: int, has_education: bool) -> int:
    if not has_education:
        return _clamp(current + 15)  # adding education helps a lot
    if current < 70:
        return _clamp(current + 10)  # adding coursework / GPA
    return _clamp(current + 3)


def _potential_overall_fit(current: int, has_summary: bool, summary_short: bool) -> int:
    uplift = 0.0
    if not has_summary:
        uplift += 10.0
    elif summary_short:
        uplift += 5.0
    return _clamp(current + uplift)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_potential_score(
    evaluation: ATSEvaluationResult,
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
) -> PotentialScoreResult:
    """Predict the maximum realistic ATS score after applying all recommendations."""

    scores = evaluation.scores
    missing_kw_count = len(evaluation.missingKeywords)
    action_count = len(evaluation.recommendedActions)

    # ── Detect resume weaknesses ────────────────────────────────────────
    has_metrics = any(
        any(c.isdigit() for c in (exp.description or ""))
        for exp in resume.experience
    )
    weak_starts = {"worked", "helped", "did", "was responsible"}
    has_weak_verbs = any(
        (exp.description or "").lower().strip().startswith(tuple(weak_starts))
        for exp in resume.experience
    )
    has_summary = bool(resume.summary and resume.summary.strip())
    summary_short = has_summary and len(resume.summary or "") < 80
    has_education = len(resume.education) > 0
    bullet_count = len(resume.experience)

    # Count missing skills from JD
    resume_skills_lower = {s.lower().strip() for s in resume.skills}
    missing_required = sum(
        1 for s in jd.requiredSkills
        if s.strip() and s.lower().strip() not in resume_skills_lower
    )
    missing_preferred = sum(
        1 for s in jd.preferredSkills
        if s.strip() and s.lower().strip() not in resume_skills_lower
    )

    # ── Per-dimension potential ─────────────────────────────────────────
    pot_skills = _potential_skills(scores.skills, missing_required, missing_preferred)
    pot_keywords = _potential_keywords(scores.keywords, missing_kw_count)
    pot_experience = _potential_experience(scores.experience, has_metrics, has_weak_verbs, bullet_count)
    pot_education = _potential_education(scores.education, has_education)
    pot_fit = _potential_overall_fit(scores.overallFit, has_summary, summary_short)

    # ── Weighted potential (same weights as LLM prompt) ─────────────────
    raw_potential = (
        pot_skills * 0.30
        + pot_keywords * 0.25
        + pot_experience * 0.25
        + pot_education * 0.10
        + pot_fit * 0.10
    )

    # ── Seniority ceiling — hard-cap unrealistic scores ─────────────────
    resume_seniority = _estimate_resume_seniority(resume)
    jd_seniority = _seniority_index(jd.seniority)
    gap = max(0, jd_seniority - resume_seniority)
    ceiling = _SENIORITY_CEILINGS.get(min(gap, 4), 75)

    # Also cap based on how many actionable items exist
    # (few actions = little room to improve)
    if action_count == 0:
        ceiling = min(ceiling, evaluation.overallScore + 3)

    potential_score = _clamp(min(raw_potential, ceiling))

    # Never predict lower than current
    potential_score = max(potential_score, evaluation.overallScore)

    improvement = potential_score - evaluation.overallScore

    return PotentialScoreResult(
        currentScore=evaluation.overallScore,
        potentialScore=potential_score,
        improvementPotential=improvement,
    )
