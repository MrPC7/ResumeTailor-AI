"""Unit tests for RecruiterEvaluation schema."""
from __future__ import annotations

import pytest
from schemas.agent_models import RecruiterEvaluation


class TestRecruiterEvaluation:
    def test_valid_evaluation(self) -> None:
        data = {
            "match_level": "strong_match",
            "hiring_confidence": 85,
            "interview_probability": 90,
            "strengths": [
                "5 years Python experience matches requirement",
                "FastAPI project demonstrates framework mastery",
            ],
            "gaps": ["No Kubernetes experience mentioned"],
            "verdict": "Strong backend candidate, recommend immediate interview",
            "reasoning": [
                "Candidate has 5 years backend experience exceeding 5-year minimum",
                "All must-have programming skills present: Python, FastAPI",
                "Missing one DevOps skill (Kubernetes) but has Docker",
            ],
        }
        evaluation = RecruiterEvaluation.model_validate(data)
        assert evaluation.match_level == "strong_match"
        assert evaluation.hiring_confidence == 85
        assert evaluation.interview_probability == 90
        assert len(evaluation.strengths) == 2
        assert len(evaluation.gaps) == 1
        assert "recommend immediate interview" in evaluation.verdict
        assert len(evaluation.reasoning) == 3

    def test_empty_evaluation_defaults(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({})
        assert evaluation.match_level == ""
        assert evaluation.hiring_confidence == 0
        assert evaluation.interview_probability == 0
        assert evaluation.strengths == []
        assert evaluation.gaps == []
        assert evaluation.verdict == ""
        assert evaluation.reasoning == []

    def test_clamps_score_above_100(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({
            "hiring_confidence": 150,
            "interview_probability": 200,
        })
        assert evaluation.hiring_confidence == 100
        assert evaluation.interview_probability == 100

    def test_clamps_score_below_0(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({
            "hiring_confidence": -10,
            "interview_probability": -5,
        })
        assert evaluation.hiring_confidence == 0
        assert evaluation.interview_probability == 0

    def test_coerces_float_scores(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({
            "hiring_confidence": 72.8,
            "interview_probability": 65.3,
        })
        assert evaluation.hiring_confidence == 72
        assert evaluation.interview_probability == 65

    def test_coerces_string_scores(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({
            "hiring_confidence": "85",
            "interview_probability": "70%",
        })
        assert evaluation.hiring_confidence == 85
        assert evaluation.interview_probability == 70

    def test_coerces_invalid_string_scores_to_zero(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({
            "hiring_confidence": "high",
            "interview_probability": "likely",
        })
        assert evaluation.hiring_confidence == 0
        assert evaluation.interview_probability == 0

    def test_match_level_normalization(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({"match_level": "Strong Match"})
        assert evaluation.match_level == "strong_match"

    def test_match_level_with_spaces(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({"match_level": "partial match"})
        assert evaluation.match_level == "partial_match"

    def test_match_level_unknown_passes_through_lowered(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({"match_level": "Excellent"})
        assert evaluation.match_level == "excellent"

    def test_verdict_coerces_list(self) -> None:
        evaluation = RecruiterEvaluation.model_validate({
            "verdict": ["Good", "candidate"]
        })
        assert evaluation.verdict == "Good; candidate"

    def test_ignores_extra_keys(self) -> None:
        data = {"match_level": "good_match", "extra_field": "ignored"}
        evaluation = RecruiterEvaluation.model_validate(data)
        assert evaluation.match_level == "good_match"
