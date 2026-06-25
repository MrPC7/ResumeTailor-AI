from __future__ import annotations

from enum import Enum


class PromptType(str, Enum):
    RESUME_EXTRACTION = "resume_extraction"
    JD_ANALYSIS = "jd_analysis"
    RESUME_CUSTOMIZATION = "resume_customization"
    COVER_LETTER = "cover_letter"
    ATS_EVALUATION = "ats_evaluation"

    # v2 multi-agent pipeline
    CANDIDATE_PROFILE_EXTRACTION = "candidate_profile_extraction"
    JOB_PROFILE_EXTRACTION = "job_profile_extraction"
