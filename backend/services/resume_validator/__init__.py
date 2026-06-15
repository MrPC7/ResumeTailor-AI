from services.llm import llm_client
from services.resume_validator.ai_verifier import AIResumeVerifier
from services.resume_validator.validator import (
    compute_resume_confidence,
    needs_ai_verification,
)

ai_verifier = AIResumeVerifier(client=llm_client)

__all__ = [
    "ai_verifier",
    "compute_resume_confidence",
    "needs_ai_verification",
]
