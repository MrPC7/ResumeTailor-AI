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
    "You are an expert resume writer and career coach specialising in ATS optimisation. "
    "Your task is to tailor resume content to a specific job description "
    "while preserving factual accuracy — never fabricate skills or experience. "
    "Return ONLY a valid JSON object. "
    "Do not include markdown code fences, backticks, or any text outside the JSON object."
)

_RESUME_CUSTOMIZATION_USER = """\
Tailor the resume below to match the job description analysis and gap analysis provided.

Critical Integrity Rules — NEVER violate under any circumstance:
- NEVER add skills, tools, or technologies that are not already present in the original resume.
- NEVER fabricate work experience, job titles, companies, durations, or achievements.
- NEVER invent projects, certifications, or degrees.
- NEVER change name, email, phone, company, position, duration, institution, degree, year, or project technologies.
- You may ONLY rewrite descriptive text — not invent new facts.

Customization Tasks (apply all five):
1. Rewrite summary: Align it with the role title, seniority, and top responsibilities from the JD.
2. Reorder skills: Move requiredSkills and preferredSkills that already exist in the resume to the front.
3. Optimize experience bullets: Rewrite descriptions to surface JD-relevant achievements; incorporate atsKeywords naturally where factually accurate.
4. Improve ATS alignment: Ensure the most impactful atsKeywords appear in the summary and experience descriptions where truthful.
5. Suggest missing keywords: For each skill in missingSkills, add a specific suggestion the candidate can act on.

Required JSON structure:
{{
  "customizedResume": {{
    "name": "unchanged",
    "email": "unchanged",
    "phone": "unchanged",
    "summary": "rewritten to target the role and seniority",
    "skills": ["reordered — requiredSkills and preferredSkills from the JD listed first, rest follow"],
    "experience": [
      {{
        "company": "unchanged",
        "position": "unchanged",
        "duration": "unchanged",
        "description": "rewritten to emphasise JD-relevant responsibilities and achievements"
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
        "description": "rewritten to highlight JD-relevant aspects where accurate",
        "technologies": ["unchanged"]
      }}
    ]
  }},
  "suggestions": [
    "Concise, actionable suggestion — one per missing skill or improvement opportunity"
  ]
}}

Resume JSON:
{resume_json}

Job Description Analysis JSON:
{jd_json}

Gap Analysis JSON:
{gap_json}"""


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
}
