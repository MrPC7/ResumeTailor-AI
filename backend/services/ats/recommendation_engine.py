"""ATS Recommendation Intelligence Engine.

Generates structured, prioritised recommendation groups from an ATS
evaluation, resume, and JD.  Every recommendation carries an impact
level and estimated point gain so the frontend can sort by value.

Deterministic — no LLM call.  Runs in < 1 ms.
"""
from __future__ import annotations

import re

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse
from services.ats.ats_models import (
    ATSEvaluationResult,
    Recommendation,
    RecommendationGroup,
    RecommendationReport,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WEAK_VERBS = {"worked", "helped", "did", "was responsible", "assisted", "participated"}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _resume_skill_set(resume: ExtractResumeResponse) -> set[str]:
    return {_normalize(s) for s in resume.skills if s.strip()}


def _missing(jd_list: list[str], have: set[str]) -> list[str]:
    return [s for s in jd_list if s.strip() and _normalize(s) not in have]


def _has_metrics(resume: ExtractResumeResponse) -> bool:
    return any(
        any(c.isdigit() for c in (exp.description or ""))
        for exp in resume.experience
    )


def _has_weak_verbs(resume: ExtractResumeResponse) -> bool:
    return any(
        any((exp.description or "").lower().strip().startswith(w) for w in _WEAK_VERBS)
        for exp in resume.experience
    )


# ---------------------------------------------------------------------------
# Group builders — each returns a RecommendationGroup (or None if empty)
# ---------------------------------------------------------------------------

def _group_missing_keywords(
    eval_result: ATSEvaluationResult,
    kw_score: int,
) -> RecommendationGroup | None:
    missing = eval_result.missingKeywords
    if not missing:
        return None
    recs: list[Recommendation] = []
    for i, kw in enumerate(missing):
        pts = 3 if kw_score < 60 else 2
        recs.append(Recommendation(
            id=f"kw-{i}",
            title=f"Add keyword: {kw}",
            description=f"Include \"{kw}\" in your resume — it is a high-value ATS keyword from the job description.",
            impactLevel="critical" if kw_score < 50 else "high",
            estimatedPoints=pts,
        ))
    return RecommendationGroup(
        groupId="missing-keywords",
        groupTitle="Missing ATS Keywords",
        recommendations=recs,
    )


def _group_missing_required_skills(
    jd: AnalyzeJDResponse,
    have: set[str],
    skills_score: int,
) -> RecommendationGroup | None:
    missing = _missing(jd.requiredSkills, have)
    if not missing:
        return None
    recs: list[Recommendation] = []
    for i, skill in enumerate(missing):
        pts = 4 if skills_score < 60 else 3
        recs.append(Recommendation(
            id=f"req-{i}",
            title=f"Add required skill: {skill}",
            description=f"\"{skill}\" is listed as a required skill. Add it to your skills section and weave it into relevant experience bullets.",
            impactLevel="critical",
            estimatedPoints=pts,
        ))
    return RecommendationGroup(
        groupId="missing-required-skills",
        groupTitle="Missing Required Skills",
        recommendations=recs,
    )


def _group_missing_preferred_skills(
    jd: AnalyzeJDResponse,
    have: set[str],
) -> RecommendationGroup | None:
    missing = _missing(jd.preferredSkills, have)
    if not missing:
        return None
    recs: list[Recommendation] = []
    for i, skill in enumerate(missing):
        recs.append(Recommendation(
            id=f"pref-{i}",
            title=f"Add preferred skill: {skill}",
            description=f"\"{skill}\" is a preferred/nice-to-have skill. Mention it if you have any exposure.",
            impactLevel="medium",
            estimatedPoints=2,
        ))
    return RecommendationGroup(
        groupId="missing-preferred-skills",
        groupTitle="Missing Preferred Skills",
        recommendations=recs,
    )


def _group_experience(
    resume: ExtractResumeResponse,
    exp_score: int,
) -> RecommendationGroup | None:
    recs: list[Recommendation] = []
    idx = 0

    if not resume.experience:
        recs.append(Recommendation(
            id=f"exp-{idx}",
            title="Add work experience",
            description="Include at least one internship, freelance project, or full-time role to demonstrate practical experience.",
            impactLevel="critical",
            estimatedPoints=5,
        ))
        idx += 1

    if resume.experience and not _has_metrics(resume):
        recs.append(Recommendation(
            id=f"exp-{idx}",
            title="Add quantifiable metrics",
            description="Include numbers in your bullet points (e.g., 'Improved API latency by 40%', 'Managed team of 5', 'Served 1M+ users').",
            impactLevel="high",
            estimatedPoints=4,
        ))
        idx += 1

    if _has_weak_verbs(resume):
        recs.append(Recommendation(
            id=f"exp-{idx}",
            title="Replace weak action verbs",
            description="Replace 'worked on', 'helped with', 'assisted' with strong verbs like 'engineered', 'optimized', 'architected', 'implemented'.",
            impactLevel="high",
            estimatedPoints=3,
        ))
        idx += 1

    # Short descriptions
    short_bullets = [
        exp for exp in resume.experience
        if len(exp.description.strip()) < 50
    ]
    if short_bullets and len(short_bullets) >= len(resume.experience) // 2:
        recs.append(Recommendation(
            id=f"exp-{idx}",
            title="Expand experience descriptions",
            description="Aim for 2–4 detailed bullet points per role. Short descriptions miss keyword-matching opportunities.",
            impactLevel="medium",
            estimatedPoints=3,
        ))
        idx += 1

    if exp_score < 70 and resume.experience:
        recs.append(Recommendation(
            id=f"exp-{idx}",
            title="Highlight measurable achievements",
            description="Add impact statements showing results (revenue generated, costs saved, performance improvements).",
            impactLevel="high",
            estimatedPoints=3,
        ))
        idx += 1

    return RecommendationGroup(
        groupId="experience-improvements",
        groupTitle="Experience Improvements",
        recommendations=recs,
    ) if recs else None


def _group_summary(
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
    fit_score: int,
) -> RecommendationGroup | None:
    recs: list[Recommendation] = []
    idx = 0
    summary = (resume.summary or "").strip()

    if not summary:
        recs.append(Recommendation(
            id=f"sum-{idx}",
            title="Add a professional summary",
            description="Write a 2–3 sentence summary at the top of your resume highlighting your key qualifications for this role.",
            impactLevel="critical",
            estimatedPoints=5,
        ))
        idx += 1
    elif len(summary) < 80:
        recs.append(Recommendation(
            id=f"sum-{idx}",
            title="Expand your summary",
            description="Your summary is too short. Aim for 2–3 sentences covering your experience level, key skills, and career focus.",
            impactLevel="high",
            estimatedPoints=3,
        ))
        idx += 1

    if summary and jd.role and _normalize(jd.role) not in _normalize(summary):
        recs.append(Recommendation(
            id=f"sum-{idx}",
            title=f"Mention target role: {jd.role}",
            description=f"Include the job title \"{jd.role}\" in your summary to signal alignment with the position.",
            impactLevel="high",
            estimatedPoints=3,
        ))
        idx += 1

    if summary and jd.requiredSkills:
        summary_lower = _normalize(summary)
        missing_in_summary = [
            s for s in jd.requiredSkills[:5]
            if _normalize(s) not in summary_lower
        ]
        if len(missing_in_summary) >= 2:
            kw_str = ", ".join(missing_in_summary[:4])
            recs.append(Recommendation(
                id=f"sum-{idx}",
                title="Add key skills to summary",
                description=f"Mention these top required skills in your summary: {kw_str}.",
                impactLevel="medium",
                estimatedPoints=2,
            ))
            idx += 1

    return RecommendationGroup(
        groupId="summary-improvements",
        groupTitle="Summary Improvements",
        recommendations=recs,
    ) if recs else None


def _group_skills(
    resume: ExtractResumeResponse,
    skills_score: int,
) -> RecommendationGroup | None:
    recs: list[Recommendation] = []
    idx = 0

    if len(resume.skills) < 5:
        recs.append(Recommendation(
            id=f"skl-{idx}",
            title="Expand skills list",
            description="List 8–15 relevant technical skills. ATS systems match against your skills section first.",
            impactLevel="high",
            estimatedPoints=4,
        ))
        idx += 1

    generic = {"communication", "teamwork", "problem solving", "leadership", "management", "time management"}
    resume_norm = {_normalize(s) for s in resume.skills}
    if resume.skills and resume_norm.issubset(generic):
        recs.append(Recommendation(
            id=f"skl-{idx}",
            title="Add technical skills",
            description="Your skills are all soft skills. ATS systems prioritise hard/technical skills — add specific tools, languages, and frameworks.",
            impactLevel="critical",
            estimatedPoints=5,
        ))
        idx += 1

    if len(resume.skills) > 20:
        recs.append(Recommendation(
            id=f"skl-{idx}",
            title="Organise skills into categories",
            description="Group skills into categories (Languages, Frameworks, Cloud, Databases) for better readability and ATS parsing.",
            impactLevel="low",
            estimatedPoints=1,
        ))
        idx += 1

    return RecommendationGroup(
        groupId="skills-improvements",
        groupTitle="Skills Section Improvements",
        recommendations=recs,
    ) if recs else None


def _group_projects(
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
) -> RecommendationGroup | None:
    recs: list[Recommendation] = []
    idx = 0

    if not resume.projects:
        recs.append(Recommendation(
            id=f"prj-{idx}",
            title="Add projects section",
            description="Include 2–3 relevant projects to showcase hands-on experience with technologies mentioned in the job description.",
            impactLevel="high",
            estimatedPoints=3,
        ))
        idx += 1
    else:
        missing_tech = [
            p for p in resume.projects if not p.technologies
        ]
        if missing_tech:
            recs.append(Recommendation(
                id=f"prj-{idx}",
                title="List technologies per project",
                description="Add a technologies list to each project so ATS can match them against job requirements.",
                impactLevel="medium",
                estimatedPoints=2,
            ))
            idx += 1

        short_desc = [p for p in resume.projects if len(p.description.strip()) < 30]
        if short_desc:
            recs.append(Recommendation(
                id=f"prj-{idx}",
                title="Expand project descriptions",
                description="Add detail about what you built, your role, and the impact. Short descriptions miss keyword matches.",
                impactLevel="medium",
                estimatedPoints=2,
            ))
            idx += 1

        if jd.requiredSkills:
            proj_techs = {_normalize(t) for p in resume.projects for t in p.technologies}
            has_jd_tech = any(_normalize(s) in proj_techs for s in jd.requiredSkills)
            if not has_jd_tech:
                recs.append(Recommendation(
                    id=f"prj-{idx}",
                    title="Add JD-relevant project technologies",
                    description="None of your projects use technologies from the job description. Add or highlight projects using required skills.",
                    impactLevel="high",
                    estimatedPoints=3,
                ))
                idx += 1

    return RecommendationGroup(
        groupId="project-improvements",
        groupTitle="Project Improvements",
        recommendations=recs,
    ) if recs else None


def _group_education(
    resume: ExtractResumeResponse,
    edu_score: int,
) -> RecommendationGroup | None:
    recs: list[Recommendation] = []
    idx = 0

    if not resume.education:
        recs.append(Recommendation(
            id=f"edu-{idx}",
            title="Add education section",
            description="Include your highest degree, institution, and graduation year. ATS systems look for education matches.",
            impactLevel="high",
            estimatedPoints=4,
        ))
        idx += 1
    else:
        missing_degree = any(not e.degree.strip() for e in resume.education)
        if missing_degree:
            recs.append(Recommendation(
                id=f"edu-{idx}",
                title="Add degree titles",
                description="Specify your degree name (e.g., 'B.S. Computer Science') for each education entry.",
                impactLevel="medium",
                estimatedPoints=2,
            ))
            idx += 1

        missing_year = any(not e.year.strip() for e in resume.education)
        if missing_year:
            recs.append(Recommendation(
                id=f"edu-{idx}",
                title="Add graduation years",
                description="Include your graduation year for each education entry.",
                impactLevel="low",
                estimatedPoints=1,
            ))
            idx += 1

        if edu_score < 70:
            recs.append(Recommendation(
                id=f"edu-{idx}",
                title="Add relevant coursework or certifications",
                description="Include relevant coursework, academic projects, certifications, or GPA if above 3.5.",
                impactLevel="medium",
                estimatedPoints=2,
            ))
            idx += 1

    return RecommendationGroup(
        groupId="education-improvements",
        groupTitle="Education Improvements",
        recommendations=recs,
    ) if recs else None


def _group_role_tailoring(
    jd: AnalyzeJDResponse,
    resume: ExtractResumeResponse,
) -> RecommendationGroup | None:
    recs: list[Recommendation] = []
    idx = 0

    if jd.role:
        recs.append(Recommendation(
            id=f"role-{idx}",
            title=f"Target role title: {jd.role}",
            description=f"Use the exact job title \"{jd.role}\" in your resume header or summary to match the ATS role filter.",
            impactLevel="high",
            estimatedPoints=3,
        ))
        idx += 1

    if jd.seniority:
        recs.append(Recommendation(
            id=f"role-{idx}",
            title=f"Reflect {jd.seniority}-level language",
            description=f"Use language appropriate for a {jd.seniority}-level role — emphasise scope, ownership, leadership, and impact at that level.",
            impactLevel="medium",
            estimatedPoints=2,
        ))
        idx += 1

    # Check responsibilities coverage
    if jd.responsibilities:
        exp_text = " ".join(
            (e.description or "") for e in resume.experience
        ).lower()
        unmatched = [
            r for r in jd.responsibilities
            if r.strip() and _normalize(r)[:20] not in exp_text
        ]
        if len(unmatched) >= 3:
            recs.append(Recommendation(
                id=f"role-{idx}",
                title="Address key responsibilities",
                description=f"At least {len(unmatched)} job responsibilities are not reflected in your experience. Rewrite bullets to address them.",
                impactLevel="high",
                estimatedPoints=3,
            ))
            idx += 1

    return RecommendationGroup(
        groupId="role-tailoring",
        groupTitle="Role-Specific Tailoring",
        recommendations=recs,
    ) if recs else None


def _group_formatting(
    resume: ExtractResumeResponse,
) -> RecommendationGroup | None:
    recs: list[Recommendation] = []
    idx = 0

    all_desc = [exp.description for exp in resume.experience if exp.description]
    if all_desc:
        avg_len = sum(len(d) for d in all_desc) / len(all_desc)
        if avg_len < 50:
            recs.append(Recommendation(
                id=f"fmt-{idx}",
                title="Use detailed bullet points",
                description="Expand experience bullets to 2–4 per role. Detailed descriptions improve keyword density.",
                impactLevel="medium",
                estimatedPoints=2,
            ))
            idx += 1

    if not resume.phone and not resume.email:
        recs.append(Recommendation(
            id=f"fmt-{idx}",
            title="Add contact information",
            description="Include your email address and phone number. Missing contact info can flag ATS parsing errors.",
            impactLevel="high",
            estimatedPoints=2,
        ))
        idx += 1
    elif not resume.phone:
        recs.append(Recommendation(
            id=f"fmt-{idx}",
            title="Add phone number",
            description="Include your phone number for complete contact information.",
            impactLevel="low",
            estimatedPoints=1,
        ))
        idx += 1
    elif not resume.email:
        recs.append(Recommendation(
            id=f"fmt-{idx}",
            title="Add email address",
            description="Include a professional email address for contact information.",
            impactLevel="low",
            estimatedPoints=1,
        ))
        idx += 1

    if not resume.name:
        recs.append(Recommendation(
            id=f"fmt-{idx}",
            title="Add your full name",
            description="Your resume is missing a name header. Add your full name at the top.",
            impactLevel="high",
            estimatedPoints=2,
        ))
        idx += 1

    return RecommendationGroup(
        groupId="ats-formatting",
        groupTitle="ATS Formatting",
        recommendations=recs,
    ) if recs else None


# ---------------------------------------------------------------------------
# Impact ordering
# ---------------------------------------------------------------------------

_IMPACT_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Raw weight multipliers by impact level — used during normalisation
_IMPACT_WEIGHT = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _sort_key(rec: Recommendation) -> tuple[int, int]:
    return (_IMPACT_ORDER.get(rec.impactLevel, 3), -rec.estimatedPoints)


# ---------------------------------------------------------------------------
# Point normalisation
# ---------------------------------------------------------------------------

def _largest_remainder_alloc(weights: list[float], budget: int) -> list[int]:
    """Allocate ``budget`` integer units proportionally to ``weights``.

    Uses the largest-remainder (Hamilton) method to ensure the total is exact.
    """
    total_w = sum(weights) or 1.0
    exact = [(w / total_w) * budget for w in weights]
    floored = [int(e) for e in exact]
    remainders = [e - f for e, f in zip(exact, floored)]

    leftover = budget - sum(floored)
    if leftover > 0:
        # Break ties by original weight (higher weight wins)
        indices = sorted(
            range(len(weights)),
            key=lambda i: (remainders[i], weights[i]),
            reverse=True,
        )
        for i in indices:
            if leftover <= 0:
                break
            floored[i] += 1
            leftover -= 1

    return floored


def _normalise_points(groups: list[RecommendationGroup], budget: int) -> None:
    """Re-distribute estimatedPoints so they sum to *exactly* ``budget``.

    Two-level allocation:
      1. Budget is split across **groups** proportional to their total weight.
      2. Each group's allocation is split across its **items** proportionally.

    This prevents one large group from hoarding all points and produces a
    visually balanced, realistic distribution.
    """
    all_recs = [r for g in groups for r in g.recommendations]
    if not all_recs or budget <= 0:
        for r in all_recs:
            r.estimatedPoints = 0
        return

    # Level 1: allocate budget to groups
    group_weights = [
        sum(
            r.estimatedPoints * _IMPACT_WEIGHT.get(r.impactLevel, 1)
            for r in g.recommendations
        )
        for g in groups
    ]
    group_budgets = _largest_remainder_alloc(
        [float(w) for w in group_weights], budget,
    )

    # Level 2: allocate each group's budget to its items
    for group, g_budget in zip(groups, group_budgets):
        if g_budget <= 0:
            for r in group.recommendations:
                r.estimatedPoints = 0
            continue

        item_weights = [
            r.estimatedPoints * _IMPACT_WEIGHT.get(r.impactLevel, 1)
            for r in group.recommendations
        ]
        item_alloc = _largest_remainder_alloc(
            [float(w) for w in item_weights], g_budget,
        )
        for rec, pts in zip(group.recommendations, item_alloc):
            rec.estimatedPoints = pts


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_recommendations(
    evaluation: ATSEvaluationResult,
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
) -> RecommendationReport:
    """Generate a structured, sorted recommendation report."""

    scores = evaluation.scores
    have = _resume_skill_set(resume)

    builders = [
        _group_missing_keywords(evaluation, scores.keywords),
        _group_missing_required_skills(jd, have, scores.skills),
        _group_missing_preferred_skills(jd, have),
        _group_experience(resume, scores.experience),
        _group_summary(resume, jd, scores.overallFit),
        _group_skills(resume, scores.skills),
        _group_projects(resume, jd),
        _group_education(resume, scores.education),
        _group_role_tailoring(jd, resume),
        _group_formatting(resume),
    ]

    groups: list[RecommendationGroup] = []

    for group in builders:
        if group is None:
            continue
        # Sort recommendations within each group by impact
        group.recommendations.sort(key=_sort_key)
        groups.append(group)

    # Budget = headroom to reach 100 from the current overall score
    budget = max(0, 100 - evaluation.overallScore)
    _normalise_points(groups, budget)

    total_gain = sum(
        r.estimatedPoints for g in groups for r in g.recommendations
    )

    # Sort groups: group with highest total estimated gain first
    groups.sort(
        key=lambda g: sum(r.estimatedPoints for r in g.recommendations),
        reverse=True,
    )

    return RecommendationReport(
        totalEstimatedGain=total_gain,
        groups=groups,
    )
