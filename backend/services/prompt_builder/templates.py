from __future__ import annotations

from dataclasses import dataclass

from services.prompt_builder.types import PromptType


@dataclass(frozen=True)
class PromptTemplate:
    system: str
    user_template: str


# ---------------------------------------------------------------------------
# Resume Extraction
# ---------------------------------------------------------------------------
_RESUME_EXTRACTION_SYSTEM = (
    "You are an expert resume parser. "
    "Extract structured information from resume text with precision. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_RESUME_EXTRACTION_USER = """\
Extract structured information from the resume text below.

Required JSON structure:
{{
  "name": "Full name of the candidate, or null if not found",
  "email": "Email address, or null if not found",
  "phone": "Phone number, or null if not found",
  "summary": "Professional summary or objective statement, or null if not found",
  "skills": ["List every skill, tool, technology, and framework mentioned anywhere in the resume"],
  "experience": [
    {{
      "company": "Company or organisation name",
      "position": "Job title or role",
      "duration": "e.g. Jan 2022 - Present  or  2019 - 2021",
      "description": "Key responsibilities and achievements in this role"
    }}
  ],
  "education": [
    {{
      "institution": "University, college, or school name",
      "degree": "Degree title and field of study",
      "year": "Graduation year or duration e.g. 2018 - 2022"
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "What the project does and your role",
      "technologies": ["Technology1", "Technology2"]
    }}
  ]
}}

Rules:
- Use null for any missing or unavailable scalar field.
- Use an empty array [] for any missing list field.
- List experience entries with the most recent position first.
- Extract every skill mentioned anywhere — do not deduplicate aggressively.

Resume Text:
{raw_text}"""


# ---------------------------------------------------------------------------
# JD Analysis
# ---------------------------------------------------------------------------
_JD_ANALYSIS_SYSTEM = (
    "You are an expert recruiter and ATS specialist. "
    "Analyze job descriptions and extract structured hiring criteria with precision. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_JD_ANALYSIS_USER = """\
Analyze the job description below and extract structured information.

Required JSON structure:
{{
  "role": "Exact job title as written in the job description",
  "seniority": "One of: Intern, Junior, Mid, Senior, Lead, Principal, Staff, Director, VP, C-Level",
  "requiredSkills": [
    "Every skill, technology, tool, or qualification explicitly marked as required or mandatory"
  ],
  "preferredSkills": [
    "Every skill, technology, tool, or qualification marked as preferred, nice-to-have, or bonus"
  ],
  "atsKeywords": [
    "High-value keywords for ATS matching: technologies, methodologies, certifications, domain terms, action verbs that appear in this JD"
  ],
  "responsibilities": [
    "Each distinct responsibility or duty listed in the job description as a concise bullet string"
  ]
}}

Rules:
- Use null only for "role" or "seniority" if genuinely absent — all list fields must always be arrays (use [] if empty).
- Infer seniority from context (years of experience, title, team size, scope) if not stated explicitly.
- Do not merge required and preferred skills — keep them strictly separate.
- atsKeywords must be the most impactful terms for resume-to-JD matching; include both technical and soft-skill keywords.
- Keep responsibilities concise — one action per string.

Job Description:
{job_description}"""


# ---------------------------------------------------------------------------
# Resume Customization
# ---------------------------------------------------------------------------
_RESUME_CUSTOMIZATION_SYSTEM = (
    "You are an expert resume writer and ATS optimisation specialist. "
    "Your task is to apply ONLY the accepted recommendations to tailor the resume. "
    "You must NEVER apply rejected recommendations. "
    "You must NEVER fabricate any information — only rewrite existing content. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_RESUME_CUSTOMIZATION_USER = """\
Apply ONLY the accepted recommendations below to tailor this resume for the target job.

═══════════════════════════════════════════
ABSOLUTE INTEGRITY RULES — VIOLATION = FAILURE
═══════════════════════════════════════════

1. NEVER apply any recommendation from the REJECTED list.
2. NEVER invent, fabricate, or hallucinate:
   - Work experience, job titles, companies, or employment durations
   - Projects that do not exist in the original resume
   - Skills, tools, or technologies not already present in the original resume
   - Certifications, degrees, institutions, or graduation years
   - Metrics, numbers, or achievements that are not in the original
3. NEVER change these identity fields: name, email, phone, company, position, duration, institution, degree, year, project name, project technologies.
4. You may ONLY:
   - Rewrite summary text to align with the target role
   - Rewrite experience bullet descriptions using JD-relevant phrasing (from EXISTING facts only)
   - Rewrite project descriptions to highlight JD-relevant aspects (from EXISTING facts only)
   - Reorder skills so JD-relevant skills appear first (do NOT add new skills)
   - Incorporate ATS keywords into existing descriptions WHERE factually accurate

═══════════════════════════════════════════
LENGTH PRESERVATION RULES — CRITICAL
═══════════════════════════════════════════

5. Preserve the EXACT same number of sections as the original resume.
6. Preserve the EXACT same number of experience entries and project entries — do NOT add new ones.
7. Do NOT add new sections, bullet points, or list items that did not exist in the original.
8. Do NOT significantly increase content length — prefer REWRITING over EXPANDING.
9. Keep descriptions concise and ATS-friendly — remove verbosity, not add it.
10. Target a ONE-PAGE resume whenever possible — brevity is critical.
11. Each experience description should be ≤ 3 concise sentences.
12. Summary should be ≤ 2 sentences.

═══════════════════════════════════════════
ACCEPTED RECOMMENDATIONS (apply these)
═══════════════════════════════════════════
{accepted_json}

═══════════════════════════════════════════
REJECTED RECOMMENDATIONS (DO NOT apply)
═══════════════════════════════════════════
{rejected_json}

═══════════════════════════════════════════

Required JSON structure:
{{
  "customizedResume": {{
    "name": "unchanged from original",
    "email": "unchanged from original",
    "phone": "unchanged from original",
    "summary": "rewritten ONLY if an accepted recommendation requires it, otherwise unchanged",
    "skills": ["reordered — JD-relevant skills first, NO new skills added"],
    "experience": [
      {{
        "company": "unchanged",
        "position": "unchanged",
        "duration": "unchanged",
        "description": "rewritten ONLY to apply accepted recommendations using existing facts"
      }}
    ],
    "education": [
      {{
        "institution": "unchanged",
        "degree": "unchanged",
        "year": "unchanged"
      }}
    ],
    "projects": [
      {{
        "name": "unchanged",
        "description": "rewritten ONLY to apply accepted recommendations using existing facts",
        "technologies": ["unchanged — same list as original"]
      }}
    ]
  }},
  "suggestions": [
    "Actionable advice for improvements the candidate must do manually (e.g. learn a missing skill, get a certification)"
  ]
}}

Original Resume JSON:
{resume_json}

Target Job Description Analysis JSON:
{jd_json}"""


# ---------------------------------------------------------------------------
# Cover Letter Generation
# ---------------------------------------------------------------------------
_COVER_LETTER_SYSTEM = (
    "You are a professional cover-letter writer. "
    "Your task is to generate a polished, job-specific cover letter using ONLY information present in the candidate's resume. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_COVER_LETTER_USER = """\
Generate a professional cover letter for the candidate below, tailored to the target job description.

═══════════════════════════════════════════
ABSOLUTE INTEGRITY RULES — VIOLATION = FAILURE
═══════════════════════════════════════════

1. NEVER invent, fabricate, or hallucinate:
   - Work experience, job titles, companies, or employment durations
   - Projects that do not exist in the resume
   - Skills, tools, or technologies not present in the resume
   - Certifications, degrees, institutions, or achievements not in the resume
   - Metrics, numbers, or results that are not in the resume
2. Use ONLY facts, skills, experience, and projects from the provided resume JSON.
3. The letter must be professionally formatted, 3-4 paragraphs.
4. Opening paragraph: express enthusiasm for the specific role and company (use role from JD).
5. Body paragraphs: connect the candidate's REAL experience and skills to key job requirements.
6. Closing paragraph: call to action, express eagerness for an interview.
7. Highlight the candidate's strongest matching skills and most relevant experience.
8. Tone: confident, professional, concise. Avoid generic filler phrases.

═══════════════════════════════════════════

Required JSON structure:
{{{{
  "coverLetter": "The full cover letter text with proper paragraph breaks (use \\n\\n between paragraphs)",
  "strengthsHighlighted": [
    "Each specific strength from the resume that was highlighted in the letter"
  ],
  "matchingSkillsUsed": [
    "Each skill from the resume that directly matches a JD requirement and was referenced in the letter"
  ]
}}}}

Candidate Resume JSON:
{resume_json}

Target Job Description Analysis JSON:
{jd_json}"""


# ---------------------------------------------------------------------------
# ATS Evaluation
# ---------------------------------------------------------------------------
_ATS_EVALUATION_SYSTEM = (
    "You are an expert ATS (Applicant Tracking System) evaluator and career advisor. "
    "You analyse resumes against job descriptions with the same rigour as enterprise "
    "ATS software.  Return ONLY a valid JSON object — no markdown fences, no extra text."
)

_ATS_EVALUATION_USER = """\
Evaluate the resume below against the job description analysis.

Score each dimension from 0 to 100:

1. **skills** — How well the candidate's skills match required and preferred skills.
2. **keywords** — Coverage of ATS keywords from the JD found in the resume.
3. **experience** — Relevance, seniority, and depth of work experience to the role.
4. **education** — Alignment of education background with job requirements.
5. **overallFit** — Holistic fit considering culture, domain, and transferable skills.

Also provide:
- **overallScore** — Weighted composite (skills 30%, keywords 25%, experience 25%, education 10%, overallFit 10%).
- **confidence** — Your confidence in the evaluation accuracy (0–100).
- **strengths** — Top 3–5 resume strengths for this role.
- **weaknesses** — Top 3–5 gaps or weaknesses.
- **matchedKeywords** — Specific keywords/skills from the JD that ARE found in the resume.
- **missingKeywords** — Specific keywords/skills from the JD missing in the resume.
- **recommendedActions** — 5–8 concrete, actionable steps to improve ATS compatibility.

Required JSON structure:
{{
  "overallScore": <int 0-100>,
  "confidence": <int 0-100>,
  "scores": {{
    "skills": <int 0-100>,
    "keywords": <int 0-100>,
    "experience": <int 0-100>,
    "education": <int 0-100>,
    "overallFit": <int 0-100>
  }},
  "strengths": ["..."],
  "weaknesses": ["..."],
  "matchedKeywords": ["..."],
  "missingKeywords": ["..."],
  "recommendedActions": ["..."]
}}

Rules:
- Base scores on factual evidence in the resume — do not fabricate.
- matchedKeywords must only contain terms that genuinely appear in BOTH the JD and the resume.
- missingKeywords must only contain terms that genuinely appear in the JD but not the resume.
- recommendedActions must be specific and actionable (e.g. "Add Python to your skills section").
- If information is insufficient for a dimension, score conservatively and explain in weaknesses.

Resume JSON:
{resume_json}

Job Description Analysis JSON:
{jd_json}"""


# ---------------------------------------------------------------------------
# Candidate Profile Extraction (v2 multi-agent)
# ---------------------------------------------------------------------------
_CANDIDATE_PROFILE_SYSTEM = (
    "You are an expert resume analyst. "
    "Extract factual, structured information from raw resume text. "
    "Do NOT evaluate, score, or make judgments — only extract facts. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_CANDIDATE_PROFILE_USER = """\
Extract a structured candidate profile from the resume text below.

Focus on factual extraction only — do NOT score or evaluate.

Required JSON structure:
{{
  "skills": [
    {{
      "name": "Skill or technology name",
      "category": "One of: Programming Language, Framework, Database, Cloud, DevOps, Tool, Soft Skill, Domain, Other"
    }}
  ],
  "work_experience": [
    {{
      "company": "Company name",
      "position": "Job title",
      "duration": "e.g. Jan 2022 - Present or 2019 - 2021",
      "responsibilities": ["Each key responsibility or achievement as a separate string"],
      "technologies": ["Technologies used in this role"]
    }}
  ],
  "education": [
    {{
      "institution": "University or school name",
      "degree": "Degree title (e.g. B.Tech, M.Sc, MBA)",
      "field_of_study": "Field or major (e.g. Computer Science)",
      "year": "Graduation year or duration"
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "What the project does",
      "technologies": ["Tech1", "Tech2"],
      "role": "Candidate's role in the project"
    }}
  ],
  "certifications": [
    {{
      "name": "Certification name",
      "issuer": "Issuing organization",
      "year": "Year obtained or expiry"
    }}
  ],
  "total_years_experience": <number or null if cannot be determined>,
  "primary_domain": "The candidate's primary professional domain (e.g. Backend Development, Data Science, DevOps)"
}}

Rules:
- Extract ALL skills mentioned anywhere in the resume — do not skip any.
- Categorize each skill into exactly one category.
- List work experience with most recent first.
- Extract individual responsibilities as separate list items, not merged paragraphs.
- List technologies per role based on what's mentioned in that specific role.
- Use null for total_years_experience only if it truly cannot be inferred from dates.
- Use empty arrays [] for any missing list fields.
- Do NOT fabricate or infer information not present in the text.

Resume Text:
{raw_text}"""


# ---------------------------------------------------------------------------
# Job Profile Extraction (v2 multi-agent)
# ---------------------------------------------------------------------------
_JOB_PROFILE_SYSTEM = (
    "You are an expert technical recruiter and job description analyst. "
    "Extract structured, factual information from job descriptions. "
    "Do NOT evaluate or score — only extract facts. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_JOB_PROFILE_USER = """\
Extract a structured job profile from the job description below.

Focus on factual extraction only — do NOT evaluate or score candidates.

Required JSON structure:
{{
  "role": "Exact job title as stated in the JD",
  "seniority": "One of: Intern, Junior, Mid, Senior, Lead, Principal, Staff, Director, VP, C-Level",
  "must_have_skills": [
    {{
      "name": "Skill or technology explicitly marked as required/mandatory",
      "category": "One of: Programming Language, Framework, Database, Cloud, DevOps, Tool, Soft Skill, Domain, Other"
    }}
  ],
  "preferred_skills": [
    {{
      "name": "Skill or technology marked as preferred/nice-to-have/bonus",
      "category": "One of: Programming Language, Framework, Database, Cloud, DevOps, Tool, Soft Skill, Domain, Other"
    }}
  ],
  "responsibilities": [
    {{
      "description": "A single responsibility or duty as a concise statement",
      "priority": "One of: high, medium, low — based on emphasis and ordering in the JD"
    }}
  ],
  "experience_required": {{
    "min_years": <number or null if not specified>,
    "max_years": <number or null if not specified>,
    "domain": "Required domain of experience (e.g. Backend Development, Machine Learning)"
  }}
}}

Rules:
- must_have_skills: ONLY skills explicitly stated as required, mandatory, or essential.
- preferred_skills: ONLY skills stated as preferred, nice-to-have, bonus, or a plus.
- Do NOT put the same skill in both must_have and preferred — pick the stronger signal.
- Categorize each skill into exactly one category.
- responsibilities: Extract each distinct duty as a separate item. First-listed or emphasized items are "high" priority.
- seniority: Infer from title, years required, and scope if not stated explicitly.
- experience_required.min_years: Extract the minimum years required (e.g. "3+ years" → 3.0).
- experience_required.max_years: Extract maximum if stated (e.g. "3-5 years" → max 5.0), otherwise null.
- Use null for any numeric field that cannot be determined.
- Use empty arrays [] for any missing list fields.
- Do NOT fabricate information not present in the text.

Job Description:
{job_description}"""


# ---------------------------------------------------------------------------
# Recruiter Evaluation (v2 multi-agent)
# ---------------------------------------------------------------------------
_RECRUITER_EVALUATION_SYSTEM = (
    "You are a Senior Technical Recruiter with 15+ years of hiring experience. "
    "Evaluate candidates strictly based on evidence presented in their profile. "
    "You must NEVER hallucinate, infer, or assume experience not explicitly stated. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_RECRUITER_EVALUATION_USER = """\
Evaluate this candidate against the job requirements as a Senior Technical Recruiter.

═══════════════════════════════════════════
EVALUATION RULES — STRICT COMPLIANCE REQUIRED
═══════════════════════════════════════════

1. Use ONLY evidence from the Candidate Profile. Do NOT assume or infer unstated experience.
2. Penalize heavily for missing MUST-HAVE skills — each missing critical skill reduces confidence significantly.
3. Reward strong project evidence — real projects demonstrating required skills are high-signal.
4. Preferred skills are bonus points only — never penalize for missing preferred skills.
5. Experience years matter — if min_years required exceeds candidate's total, flag it as a gap.
6. Every score MUST be justified in the reasoning array.
7. match_level must be one of: strong_match, good_match, partial_match, weak_match, no_match.

═══════════════════════════════════════════
SCORING GUIDELINES
═══════════════════════════════════════════

hiring_confidence (0-100):
- 80-100: Candidate meets all must-have skills + has relevant experience depth
- 60-79: Meets most must-have skills, minor gaps compensated by strong evidence elsewhere
- 40-59: Missing 2-3 critical skills but has transferable experience
- 20-39: Missing majority of critical requirements
- 0-19: Fundamentally misaligned profile

interview_probability (0-100):
- 80-100: Would immediately shortlist for interview
- 60-79: Would likely advance to phone screen
- 40-59: Borderline — depends on candidate pool quality
- 20-39: Would probably pass unless pool is thin
- 0-19: Would not advance

match_level mapping:
- strong_match: hiring_confidence >= 80
- good_match: hiring_confidence 60-79
- partial_match: hiring_confidence 40-59
- weak_match: hiring_confidence 20-39
- no_match: hiring_confidence < 20

═══════════════════════════════════════════

Required JSON structure:
{{
  "match_level": "one of: strong_match, good_match, partial_match, weak_match, no_match",
  "hiring_confidence": <int 0-100>,
  "interview_probability": <int 0-100>,
  "strengths": [
    "Each specific strength backed by evidence from the candidate profile (cite skill/project/experience)"
  ],
  "gaps": [
    "Each gap or missing requirement with specific skill/qualification that is absent"
  ],
  "verdict": "One-sentence hiring recommendation (e.g. 'Strong backend candidate, recommend immediate interview' or 'Missing core ML skills, not suitable for this role')",
  "reasoning": [
    "Step-by-step explanation of how each score was derived, referencing specific evidence"
  ]
}}

Rules:
- strengths must reference specific skills, projects, or experience entries from the profile.
- gaps must reference specific must-have requirements from the job profile that are missing.
- reasoning must have at least 3 entries explaining the evaluation logic.
- verdict must be a single concise sentence.
- Do NOT include generic filler — every item must be specific and evidence-based.

Candidate Profile:
{candidate_json}

Job Requirements:
{job_json}"""


# ---------------------------------------------------------------------------
# Resume Tailoring (v2 multi-agent)
# ---------------------------------------------------------------------------
_RESUME_TAILORING_SYSTEM = (
    "You are an expert resume writer and career strategist. "
    "Your task is to rewrite a resume to maximize relevance, clarity, and recruiter visibility "
    "for a specific job — guided by a recruiter's evaluation of the candidate. "
    "You must NEVER invent, fabricate, or hallucinate any experience, skill, or achievement. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_RESUME_TAILORING_USER = """\
Rewrite this resume to maximize its fit for the target job, guided by the recruiter evaluation.

═══════════════════════════════════════════
ABSOLUTE INTEGRITY RULES — VIOLATION = FAILURE
═══════════════════════════════════════════

1. NEVER invent, fabricate, or hallucinate:
   - Work experience, job titles, companies, or employment durations
   - Projects that do not exist in the candidate profile
   - Skills, tools, or technologies not present in the candidate profile
   - Certifications, degrees, institutions, or achievements not in the candidate profile
   - Metrics, numbers, or results that are not in the original data
2. NEVER change identity fields: company, position, duration, institution, degree, year, project name, project technologies.
3. You may ONLY:
   - Rewrite the summary to target the specific role
   - Rewrite experience descriptions to emphasize JD-relevant aspects using EXISTING facts
   - Rewrite project descriptions to highlight JD-relevant technologies and impact
   - Reorder skills so JD-relevant and must-have skills appear first
   - Incorporate ATS keywords into existing descriptions WHERE factually accurate
   - Address recruiter-identified GAPS by surfacing existing but underemphasized evidence

═══════════════════════════════════════════
OPTIMIZATION TARGETS
═══════════════════════════════════════════

1. RELEVANCE — Prioritize content that directly addresses must-have skills and responsibilities from the job profile.
2. CLARITY — Use concise, action-oriented language. One achievement per bullet. No filler.
3. RECRUITER VISIBILITY — Front-load the most relevant information. Address recruiter-identified strengths prominently and gaps where possible with existing evidence.

═══════════════════════════════════════════
RECRUITER GUIDANCE
═══════════════════════════════════════════

Use the recruiter evaluation to guide your rewrites:
- STRENGTHS: Amplify these in the tailored resume — make them impossible to miss.
- GAPS: Where the candidate has ANY existing evidence that partially addresses a gap, surface it clearly. If no evidence exists, do NOT fabricate — just optimize what's available.

═══════════════════════════════════════════

Required JSON structure:
{{
  "summary": "2-3 sentence professional summary targeting the specific role, using only facts from the candidate profile",
  "skills": ["Reordered skill list — must-have JD skills first, then preferred, then remaining. NO new skills added."],
  "experience": [
    {{
      "company": "unchanged",
      "position": "unchanged",
      "duration": "unchanged",
      "description": "Rewritten to emphasize JD-relevant achievements using EXISTING facts only. Concise, action-oriented. Max 3 sentences.",
      "technologies": ["Technologies from this role — unchanged list"]
    }}
  ],
  "projects": [
    {{
      "name": "unchanged",
      "description": "Rewritten to highlight JD-relevant aspects using EXISTING facts only",
      "technologies": ["unchanged — same list as original"]
    }}
  ],
  "improvements_made": [
    "Each specific change made to the resume with reasoning (e.g. 'Reordered skills to front-load Python and FastAPI as they are must-have requirements')"
  ],
  "gaps_addressed": [
    "Each recruiter-identified gap that was addressed and HOW (e.g. 'Surfaced Docker usage from Acme Corp role to partially address DevOps gap')"
  ]
}}

Rules:
- Preserve the EXACT same number of experience entries and project entries.
- Do NOT add new experience or project entries.
- skills list must contain ONLY skills already present in the candidate profile — reorder only.
- improvements_made must document every meaningful change.
- gaps_addressed must reference specific recruiter gaps and explain what was done.
- If a gap cannot be addressed with existing evidence, do NOT include it in gaps_addressed.
- Keep descriptions concise — ATS-friendly, no verbosity.

Candidate Profile:
{candidate_json}

Job Profile:
{job_json}

Recruiter Evaluation:
{evaluation_json}"""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
PROMPT_REGISTRY: dict[PromptType, PromptTemplate] = {
    PromptType.RESUME_EXTRACTION: PromptTemplate(
        system=_RESUME_EXTRACTION_SYSTEM,
        user_template=_RESUME_EXTRACTION_USER,
    ),
    PromptType.JD_ANALYSIS: PromptTemplate(
        system=_JD_ANALYSIS_SYSTEM,
        user_template=_JD_ANALYSIS_USER,
    ),
    PromptType.RESUME_CUSTOMIZATION: PromptTemplate(
        system=_RESUME_CUSTOMIZATION_SYSTEM,
        user_template=_RESUME_CUSTOMIZATION_USER,
    ),
    PromptType.COVER_LETTER: PromptTemplate(
        system=_COVER_LETTER_SYSTEM,
        user_template=_COVER_LETTER_USER,
    ),
    PromptType.ATS_EVALUATION: PromptTemplate(
        system=_ATS_EVALUATION_SYSTEM,
        user_template=_ATS_EVALUATION_USER,
    ),
    PromptType.CANDIDATE_PROFILE_EXTRACTION: PromptTemplate(
        system=_CANDIDATE_PROFILE_SYSTEM,
        user_template=_CANDIDATE_PROFILE_USER,
    ),
    PromptType.JOB_PROFILE_EXTRACTION: PromptTemplate(
        system=_JOB_PROFILE_SYSTEM,
        user_template=_JOB_PROFILE_USER,
    ),
    PromptType.RECRUITER_EVALUATION: PromptTemplate(
        system=_RECRUITER_EVALUATION_SYSTEM,
        user_template=_RECRUITER_EVALUATION_USER,
    ),
    PromptType.RESUME_TAILORING: PromptTemplate(
        system=_RESUME_TAILORING_SYSTEM,
        user_template=_RESUME_TAILORING_USER,
    ),
}
