from __future__ import annotations

import re
from datetime import datetime, timezone

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse


def _current_year() -> int:
    return datetime.now(tz=timezone.utc).year

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


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _tokenize(text: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9+.#\-\s]", " ", text.lower())
    tokens = {token for token in cleaned.split() if len(token) > 1}
    return tokens


def _collect_resume_terms(resume: ExtractResumeResponse) -> set[str]:
    terms: set[str] = set()

    if resume.summary:
        terms.update(_tokenize(resume.summary))

    terms.update(_normalize(skill) for skill in resume.skills if skill)

    for experience in resume.experience:
        terms.update(_tokenize(experience.position))
        terms.update(_tokenize(experience.description))
        terms.update(_tokenize(experience.company))

    for education in resume.education:
        terms.update(_tokenize(education.degree))
        terms.update(_tokenize(education.institution))

    for project in resume.projects:
        terms.update(_tokenize(project.name))
        terms.update(_tokenize(project.description))
        terms.update(_normalize(tech) for tech in project.technologies if tech)

    return {term for term in terms if term}


def _compute_list_match_score(candidate_terms: set[str], targets: list[str]) -> float:
    normalized_targets = [_normalize(item) for item in targets if item.strip()]
    if not normalized_targets:
        return 100.0

    matches = 0
    for target in normalized_targets:
        target_tokens = _tokenize(target)
        has_full_phrase = target in candidate_terms

        if has_full_phrase:
            matches += 1
            continue

        # For multi-word skills, require >=75% token overlap to avoid
        # false positives from single shared words (e.g. "machine" matching
        # "machine learning").
        if target_tokens:
            overlap = target_tokens.intersection(candidate_terms)
            ratio = len(overlap) / len(target_tokens)
            threshold = 0.75 if len(target_tokens) > 1 else 0.0
            if ratio > threshold:
                matches += 1

    return (matches / len(normalized_targets)) * 100.0


def _extract_years(duration: str) -> list[int]:
    values = [int(value) for value in re.findall(r"\b(19\d{2}|20\d{2})\b", duration)]
    return [year for year in values if 1950 <= year <= _current_year() + 1]


def _estimate_experience_years(resume: ExtractResumeResponse) -> float:
    all_years: list[int] = []

    for item in resume.experience:
        all_years.extend(_extract_years(item.duration))

    if all_years:
        span = (max(all_years) - min(all_years)) + 1
        return max(0.0, float(span))

    return float(len(resume.experience)) * 1.5


def _compute_experience_score(resume: ExtractResumeResponse, jd: AnalyzeJDResponse) -> float:
    seniority = _normalize(jd.seniority) if jd.seniority else ""
    required_years = SENIORITY_MIN_YEARS.get(seniority)

    if required_years is None:
        # When JD seniority is unavailable/unknown, use a neutral score.
        return 60.0

    resume_years = _estimate_experience_years(resume)
    if required_years == 0:
        return 100.0

    return min(100.0, (resume_years / required_years) * 100.0)


def calculate_match_scores(
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
) -> tuple[int, int, int, int]:
    resume_terms = _collect_resume_terms(resume)

    required_score = _compute_list_match_score(resume_terms, jd.requiredSkills)
    preferred_score = _compute_list_match_score(resume_terms, jd.preferredSkills)
    skill_score = (required_score * 0.8) + (preferred_score * 0.2)

    keyword_score = _compute_list_match_score(resume_terms, jd.atsKeywords)
    experience_score = _compute_experience_score(resume, jd)

    overall_score = (skill_score * 0.45) + (keyword_score * 0.35) + (experience_score * 0.20)

    return (
        _clamp_score(overall_score),
        _clamp_score(skill_score),
        _clamp_score(keyword_score),
        _clamp_score(experience_score),
    )
