from __future__ import annotations

import re

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse


# ---------------------------------------------------------------------------
# Text normalization (inlined — no external dependency)
# ---------------------------------------------------------------------------

_ALIAS_REVERSE: dict[str, str] = {}
for _canonical, _aliases in {
    "react": frozenset({"react.js", "reactjs", "react js"}),
    "node.js": frozenset({"node", "nodejs", "node js"}),
    "typescript": frozenset({"ts"}),
    "javascript": frozenset({"js"}),
    "postgresql": frozenset({"postgres", "pg"}),
    "mongodb": frozenset({"mongo"}),
    "kubernetes": frozenset({"k8s"}),
    "amazon web services": frozenset({"aws"}),
    "google cloud platform": frozenset({"gcp", "google cloud"}),
    "microsoft azure": frozenset({"azure"}),
    "continuous integration": frozenset({"ci/cd", "ci cd", "cicd"}),
    "machine learning": frozenset({"ml"}),
    "artificial intelligence": frozenset({"ai"}),
    "natural language processing": frozenset({"nlp"}),
    "large language model": frozenset({"llm", "llms"}),
    "next.js": frozenset({"nextjs", "next js"}),
}.items():
    for _alias in _aliases:
        _ALIAS_REVERSE[_alias] = _canonical


def _normalize(term: str) -> str:
    cleaned = re.sub(r"\s+", " ", term.strip().lower())
    return _ALIAS_REVERSE.get(cleaned, cleaned)


def _tokenize(text: str) -> set[str]:
    raw = re.sub(r"[^a-z0-9+.#\-\s]", " ", _normalize(text))
    return {t for t in raw.split() if len(t) > 1}


def _collect_resume_terms(resume: ExtractResumeResponse) -> set[str]:
    """Collect a flat set of normalized tokens from all resume text."""
    tokens: set[str] = set()
    for skill in resume.skills:
        tokens.update(_tokenize(skill))
    if resume.summary:
        tokens.update(_tokenize(resume.summary))
    for exp in resume.experience:
        if exp.position:
            tokens.update(_tokenize(exp.position))
        if exp.description:
            tokens.update(_tokenize(exp.description))
    for proj in resume.projects:
        if proj.description:
            tokens.update(_tokenize(proj.description))
        for tech in proj.technologies:
            tokens.update(_tokenize(tech))
    return tokens


def _classify_skills(
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
) -> tuple[list[str], list[str]]:
    resume_terms = _collect_resume_terms(resume)

    matched: list[str] = []
    missing: list[str] = []

    all_jd_skills = list(dict.fromkeys(
        jd.requiredSkills + jd.preferredSkills
    ))

    for skill in all_jd_skills:
        if not skill.strip():
            continue

        normalized = _normalize(skill)
        tokens = set(normalized.split())

        # A skill is matched if the full normalized phrase is present,
        # or if every meaningful word in the skill name exists in resume terms.
        is_matched = normalized in resume_terms or tokens.issubset(resume_terms)

        if is_matched:
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def _build_recommendations(
    missing_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
) -> list[str]:
    recommendations: list[str] = []

    required_set = {_normalize(s) for s in required_skills if s.strip()}
    preferred_set = {_normalize(s) for s in preferred_skills if s.strip()}

    missing_required = [s for s in missing_skills if _normalize(s) in required_set]
    missing_preferred = [s for s in missing_skills if _normalize(s) in preferred_set]

    for skill in missing_required:
        recommendations.append(
            f"Add '{skill}' to your resume — it is a required skill for this role."
        )

    for skill in missing_preferred:
        recommendations.append(
            f"Consider adding '{skill}' to your resume — it is listed as a preferred skill."
        )

    if missing_required:
        recommendations.append(
            "Highlight projects or experience where you used the missing required skills, "
            "even if indirectly."
        )

    if missing_preferred:
        recommendations.append(
            "Preferred skills can differentiate you from other candidates — "
            "mention relevant exposure even if limited."
        )

    return recommendations


def compute_gap(
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
) -> tuple[list[str], list[str], list[str]]:
    matched, missing = _classify_skills(resume, jd)
    recommendations = _build_recommendations(missing, jd.requiredSkills, jd.preferredSkills)

    return matched, missing, recommendations
