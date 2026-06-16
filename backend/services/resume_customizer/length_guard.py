"""Resume length analysis and compression to preserve A4 layout."""

from __future__ import annotations

from dataclasses import dataclass

from schemas.extract_resume import ExtractResumeResponse
from services.llm import LLMClient

# A4 single-page budget: ~3200 chars renders safely within margins at 11pt.
A4_CHAR_BUDGET = 3200
LENGTH_OVERFLOW_THRESHOLD = 0.15  # 15% max increase allowed


@dataclass
class ResumeMetrics:
    section_count: int
    bullet_count: int
    total_length: int


def measure_resume(resume: ExtractResumeResponse) -> ResumeMetrics:
    """Measure section count, bullet count, and total content length."""
    sections = 0
    bullets = 0
    total = 0

    if resume.summary:
        sections += 1
        total += len(resume.summary)

    if resume.skills:
        sections += 1
        total += sum(len(s) for s in resume.skills)

    if resume.experience:
        sections += 1
        for exp in resume.experience:
            bullets += 1
            total += len(exp.description or "")
            total += len(exp.position or "") + len(exp.company or "") + len(exp.duration or "")

    if resume.education:
        sections += 1
        for edu in resume.education:
            total += len(edu.degree or "") + len(edu.institution or "") + len(edu.year or "")

    if resume.projects:
        sections += 1
        for proj in resume.projects:
            bullets += 1
            total += len(proj.description or "")
            total += len(proj.name or "")
            total += sum(len(t) for t in (proj.technologies or []))

    return ResumeMetrics(section_count=sections, bullet_count=bullets, total_length=total)


def needs_compression(original: ResumeMetrics, customized: ResumeMetrics) -> bool:
    """Return True if customized resume exceeds length threshold."""
    if original.total_length == 0:
        return False
    increase = (customized.total_length - original.total_length) / original.total_length
    return increase > LENGTH_OVERFLOW_THRESHOLD


def estimate_pdf_overflow(resume: ExtractResumeResponse) -> bool:
    """Return True if rendered content would likely overflow a single A4 page."""
    metrics = measure_resume(resume)
    return metrics.total_length > A4_CHAR_BUDGET


_COMPRESSION_PROMPT = """\
You are a resume compression specialist. The resume below exceeds the allowed length.
Compress it while following these rules strictly:

1. Keep ALL ATS keywords intact — do not remove technical terms or tools.
2. Remove verbosity, filler words, and redundant phrases.
3. Preserve quantified achievements and metrics (numbers, percentages, dollar amounts).
4. Preserve all section structure — do not remove or add sections.
5. Keep the same number of experience and project entries.
6. Target total content that fits on a single A4 page (~3200 characters max).
7. Return the EXACT same JSON structure as provided.

Return ONLY a valid JSON object with the same schema as the input.

Resume JSON:
{resume_json}"""


async def compress_resume(
    client: LLMClient,
    resume: ExtractResumeResponse,
) -> ExtractResumeResponse:
    """Run a compression pass on the resume via LLM to fit A4 constraints."""
    import json
    from pydantic import ValidationError

    resume_json = json.dumps(resume.model_dump(), indent=2)
    prompt = _COMPRESSION_PROMPT.format(resume_json=resume_json)

    try:
        raw = await client.generate_json(prompt)
        compressed = ExtractResumeResponse.model_validate(raw)
        # Preserve identity fields
        compressed.name = resume.name
        compressed.email = resume.email
        compressed.phone = resume.phone
        compressed.education = resume.education
        return compressed
    except (ValidationError, Exception):
        # Fail-open: return original if compression fails
        return resume
