"""ATS evaluation prompt builder.

Constructs structured prompts for LLM-based ATS scoring.
All prompt text lives here — no hardcoded prompts elsewhere.
"""
from __future__ import annotations

import json

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse

_SYSTEM_PROMPT = (
    "You are an expert ATS (Applicant Tracking System) evaluator and career advisor. "
    "You analyse resumes against job descriptions with the same rigour as enterprise "
    "ATS software.  Return ONLY a valid JSON object — no markdown fences, no extra text."
)

_USER_TEMPLATE = """\
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
  "missingKeywords": ["..."],
  "recommendedActions": ["..."]
}}

Rules:
- Base scores on factual evidence in the resume — do not fabricate.
- missingKeywords must only contain terms that genuinely appear in the JD but not the resume.
- recommendedActions must be specific and actionable (e.g. "Add Python to your skills section").
- If information is insufficient for a dimension, score conservatively and explain in weaknesses.

Resume JSON:
{resume_json}

Job Description Analysis JSON:
{jd_json}"""


def build_ats_evaluation_prompt(
    resume: ExtractResumeResponse,
    jd: AnalyzeJDResponse,
) -> str:
    """Build a single combined prompt for ATS evaluation."""
    resume_json = json.dumps(resume.model_dump(), indent=2)
    jd_json = json.dumps(jd.model_dump(), indent=2)
    user = _USER_TEMPLATE.format(resume_json=resume_json, jd_json=jd_json)
    return f"{_SYSTEM_PROMPT}\n\n{user}"
