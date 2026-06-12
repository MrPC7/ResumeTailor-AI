from __future__ import annotations

_PROMPT_TEMPLATE = """\
You are an expert recruiter and ATS specialist. Analyze the job description provided and extract structured information.

Return ONLY a valid JSON object. Do not include markdown code fences, backticks, or any text outside the JSON object.

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


def build_jd_analysis_prompt(job_description: str) -> str:
    return _PROMPT_TEMPLATE.format(job_description=job_description)
