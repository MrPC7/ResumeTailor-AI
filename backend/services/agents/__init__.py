"""Multi-agent services — domain-specific agents for the evaluation pipeline."""
from __future__ import annotations

from services.agents.resume_analyzer import resume_analyzer_agent
from services.agents.jd_analyzer import jd_analyzer_agent
from services.agents.recruiter import recruiter_agent
from services.agents.resume_tailor import resume_tailor_agent

__all__ = [
    "resume_analyzer_agent",
    "jd_analyzer_agent",
    "recruiter_agent",
    "resume_tailor_agent",
]
