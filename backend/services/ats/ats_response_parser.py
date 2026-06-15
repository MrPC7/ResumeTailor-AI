"""ATS response parser — validates and normalises LLM JSON output."""
from __future__ import annotations

from pydantic import ValidationError

from schemas.ats_models import ATSEvaluationResult


class ATSParseError(Exception):
    """Raised when the LLM response cannot be parsed into a valid result."""


def parse_ats_response(raw: dict[str, object]) -> ATSEvaluationResult:
    """Validate raw LLM JSON against the Pydantic model.

    Raises:
        ATSParseError: If validation fails.
    """
    try:
        return ATSEvaluationResult.model_validate(raw)
    except ValidationError as exc:
        raise ATSParseError(
            f"LLM returned invalid ATS evaluation structure: {exc.error_count()} error(s)."
        ) from exc
