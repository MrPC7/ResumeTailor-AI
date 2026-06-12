from __future__ import annotations

from enum import Enum


class PromptType(str, Enum):
    RESUME_EXTRACTION = "resume_extraction"
    JD_ANALYSIS = "jd_analysis"
    RESUME_CUSTOMIZATION = "resume_customization"
