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
}
