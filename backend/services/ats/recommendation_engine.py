"""Comprehensive rule-based recommendation engine.

Generates thorough, grouped recommendations that cover every area needed
to push an ATS score toward 90+.  Every gap — skills, keywords, experience,
education, summary, projects, responsibilities, formatting — produces a
selectable recommendation group.
"""
from __future__ import annotations

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse
from services.ats.keyword_matcher import keyword_matches, build_resume_term_set, normalize
from services.ats.models import RecommendationGroup


def _build_term_sets(
    resume: ExtractResumeResponse,
) -> tuple[set[str], set[str]]:
    """Build full_phrases + token_pool from all resume content."""
    text_blocks: list[str] = []
    if resume.summary:
        text_blocks.append(resume.summary)
    for exp in resume.experience:
        text_blocks.extend(filter(None, [exp.position, exp.company, exp.description]))
    for edu in resume.education:
        text_blocks.extend(filter(None, [edu.degree, edu.institution]))
    for proj in resume.projects:
        text_blocks.extend(filter(None, [proj.name, proj.description]))
        text_blocks.extend(proj.technologies)
    return build_resume_term_set(resume.skills, text_blocks)


def generate_recommendations(
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
    missing_keywords: list[str],
    skills_score: int,
    keywords_score: int,
    experience_score: int,
    education_score: int,
) -> list[RecommendationGroup]:
    groups: list[RecommendationGroup] = []
    full_phrases, token_pool = _build_term_sets(resume)

    # ── 1. Missing ATS keywords ─────────────────────────────────────────
    if missing_keywords:
        groups.append(RecommendationGroup(
            title="Add these missing ATS keywords to your resume",
            items=list(missing_keywords),
        ))

    # ── 2. Missing required skills ───────────────────────────────────────
    missing_required = [
        s for s in jd.requiredSkills
        if s.strip() and not keyword_matches(s, full_phrases, token_pool)
    ]
    if missing_required:
        groups.append(RecommendationGroup(
            title="Add these missing required skills to your skills section",
            items=missing_required,
        ))

    # ── 3. Missing preferred/nice-to-have skills ────────────────────────
    missing_preferred = [
        s for s in jd.preferredSkills
        if s.strip() and not keyword_matches(s, full_phrases, token_pool)
    ]
    if missing_preferred:
        groups.append(RecommendationGroup(
            title="Add these preferred skills if you have experience with them",
            items=missing_preferred,
        ))

    # ── 4. Weave keywords into experience bullet points ─────────────────
    if missing_keywords:
        groups.append(RecommendationGroup(
            title="Incorporate these keywords naturally into your experience bullet points",
            items=list(missing_keywords),
        ))

    # ── 5. JD responsibilities not reflected in resume ──────────────────
    missing_responsibilities = [
        r for r in jd.responsibilities
        if r.strip() and not keyword_matches(r, full_phrases, token_pool)
    ]
    if missing_responsibilities:
        groups.append(RecommendationGroup(
            title="Align your experience descriptions with these job responsibilities",
            items=missing_responsibilities,
        ))

    # ── 6. Experience section improvements ──────────────────────────────
    exp_items: list[str] = []
    has_metrics = any(
        any(c.isdigit() for c in (exp.description or ""))
        for exp in resume.experience
    )
    if not has_metrics:
        exp_items.append(
            "Add quantifiable metrics to your bullet points "
            "(e.g., 'Improved API response time by 40%', 'Managed a team of 5')"
        )
    if experience_score < 80:
        exp_items.append(
            "Add measurable achievements that demonstrate impact "
            "(e.g., 'Reduced costs by $50K/year', 'Served 1M+ users')"
        )

    # Check if experience descriptions use strong action verbs
    weak_starts = {"worked", "helped", "did", "was responsible"}
    for exp in resume.experience:
        desc_lower = (exp.description or "").lower().strip()
        if any(desc_lower.startswith(w) for w in weak_starts):
            exp_items.append(
                "Replace weak verbs ('worked on', 'helped with') with strong action verbs "
                "('engineered', 'optimized', 'architected', 'implemented')"
            )
            break

    if not resume.experience:
        exp_items.append("Add at least one work experience or internship entry")

    if exp_items:
        groups.append(RecommendationGroup(
            title="Strengthen your experience section",
            items=list(dict.fromkeys(exp_items)),  # dedupe
        ))

    # ── 7. Skills section improvements ──────────────────────────────────
    skills_items: list[str] = []
    if len(resume.skills) < 5:
        skills_items.append(
            "Expand your skills list — aim for 8–15 relevant technical skills"
        )
    # Check if skills are too generic
    generic_skills = {"communication", "teamwork", "problem solving", "leadership", "management"}
    resume_skill_set = {normalize(s) for s in resume.skills}
    only_soft = resume_skill_set.issubset(generic_skills)
    if only_soft and resume.skills:
        skills_items.append(
            "Add specific technical skills — ATS systems prioritize hard skills over soft skills"
        )
    # Suggest grouping if many skills
    if len(resume.skills) > 15:
        skills_items.append(
            "Group your skills into categories (e.g., 'Languages', 'Frameworks', 'Cloud') "
            "for better readability"
        )
    if skills_items:
        groups.append(RecommendationGroup(
            title="Improve your skills section",
            items=skills_items,
        ))

    # ── 8. Professional summary ─────────────────────────────────────────
    summary_items: list[str] = []
    if not resume.summary:
        summary_items.append("Add a 2–3 sentence professional summary at the top of your resume")
    elif len(resume.summary) < 80:
        summary_items.append(
            "Expand your professional summary to at least 2–3 sentences"
        )

    if jd.role and resume.summary and normalize(jd.role) not in normalize(resume.summary):
        summary_items.append(
            f"Mention the target role '{jd.role}' in your summary"
        )

    # Check if summary mentions key required skills
    if resume.summary and jd.requiredSkills:
        summary_norm = normalize(resume.summary)
        missing_in_summary = [
            s for s in jd.requiredSkills[:5]
            if normalize(s) not in summary_norm
        ]
        if missing_in_summary:
            summary_items.append(
                f"Mention key skills in your summary: {', '.join(missing_in_summary[:4])}"
            )

    if summary_items:
        groups.append(RecommendationGroup(
            title="Optimize your professional summary",
            items=list(dict.fromkeys(summary_items)),
        ))

    # ── 9. Education section ────────────────────────────────────────────
    edu_items: list[str] = []
    if not resume.education:
        edu_items.append("Add your education background (degree, institution, graduation year)")
    else:
        for edu in resume.education:
            if not edu.degree:
                edu_items.append("Add your degree title to each education entry")
                break
        for edu in resume.education:
            if not edu.year:
                edu_items.append("Add graduation year to each education entry")
                break
        if education_score < 70:
            edu_items.append(
                "Add relevant coursework, academic projects, or GPA if above 3.5"
            )
    if edu_items:
        groups.append(RecommendationGroup(
            title="Improve your education section",
            items=list(dict.fromkeys(edu_items)),
        ))

    # ── 10. Projects section ────────────────────────────────────────────
    proj_items: list[str] = []
    if not resume.projects:
        proj_items.append(
            "Add 2–3 relevant projects to showcase hands-on experience"
        )
    else:
        for proj in resume.projects:
            if not proj.technologies:
                proj_items.append("List technologies used in each project")
                break
        for proj in resume.projects:
            if len(proj.description) < 30:
                proj_items.append(
                    "Add detailed descriptions to your projects explaining what you built and the impact"
                )
                break
        # Check if projects use JD-relevant tech
        if jd.requiredSkills:
            proj_techs = {normalize(t) for p in resume.projects for t in p.technologies}
            matching_tech = [
                s for s in jd.requiredSkills
                if normalize(s) in proj_techs
            ]
            if not matching_tech:
                proj_items.append(
                    "Add projects that use technologies mentioned in the job description"
                )
    if proj_items:
        groups.append(RecommendationGroup(
            title="Enhance your projects section",
            items=list(dict.fromkeys(proj_items)),
        ))

    # ── 11. Role-specific tailoring ─────────────────────────────────────
    role_items: list[str] = []
    if jd.role:
        role_items.append(f"Use the job title '{jd.role}' in your resume header or summary")
    if jd.seniority:
        role_items.append(
            f"Reflect '{jd.seniority}'-level language in your descriptions "
            "(scope of work, leadership, ownership)"
        )
    if role_items:
        groups.append(RecommendationGroup(
            title="Tailor your resume for this specific role",
            items=role_items,
        ))

    # ── 12. General ATS-friendly formatting tips ────────────────────────
    format_items: list[str] = []

    # Check for consistent content
    all_descriptions = [exp.description for exp in resume.experience if exp.description]
    if all_descriptions:
        avg_len = sum(len(d) for d in all_descriptions) / len(all_descriptions)
        if avg_len < 50:
            format_items.append(
                "Expand your experience bullet points — aim for 2–4 detailed bullets per role"
            )

    if not resume.phone and not resume.email:
        format_items.append("Add your contact information (email, phone)")
    elif not resume.phone:
        format_items.append("Add your phone number to contact information")
    elif not resume.email:
        format_items.append("Add your email address to contact information")

    if format_items:
        groups.append(RecommendationGroup(
            title="Improve resume formatting for ATS compatibility",
            items=format_items,
        ))

    return groups
