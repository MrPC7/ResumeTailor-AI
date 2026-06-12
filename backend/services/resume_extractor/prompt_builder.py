from __future__ import annotations

# Braces inside the schema block are doubled to escape Python str.format().
_PROMPT_TEMPLATE = """\
You are an expert resume parser. Extract structured information from the resume text provided.

Return ONLY a valid JSON object. Do not include markdown code fences, backticks, or any text outside the JSON object.

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


def build_extraction_prompt(raw_text: str) -> str:
    return _PROMPT_TEMPLATE.format(raw_text=raw_text)
