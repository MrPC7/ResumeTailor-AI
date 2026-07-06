"""Unit tests for the JobProfile schema (agent_models)."""
from __future__ import annotations

import pytest
from schemas.agent_models import (
    ExperienceRequirement,
    JobProfile,
    PreferredSkill,
    RequiredSkill,
    Responsibility,
)


class TestRequiredSkill:
    def test_valid_skill(self) -> None:
        skill = RequiredSkill(name="Python", category="Programming Language")
        assert skill.name == "Python"
        assert skill.category == "Programming Language"

    def test_coerces_list(self) -> None:
        skill = RequiredSkill.model_validate({"name": ["Python", "3.11"], "category": "PL"})
        assert skill.name == "Python; 3.11"

    def test_defaults(self) -> None:
        skill = RequiredSkill.model_validate({})
        assert skill.name == ""
        assert skill.category == ""

    def test_ignores_extra(self) -> None:
        skill = RequiredSkill.model_validate({"name": "Go", "category": "PL", "extra": 1})
        assert skill.name == "Go"


class TestPreferredSkill:
    def test_valid_skill(self) -> None:
        skill = PreferredSkill(name="Kubernetes", category="DevOps")
        assert skill.name == "Kubernetes"

    def test_coerces_none(self) -> None:
        skill = PreferredSkill.model_validate({"name": None, "category": None})
        assert skill.name == ""


class TestResponsibility:
    def test_valid_responsibility(self) -> None:
        resp = Responsibility(description="Design microservices", priority="high")
        assert resp.description == "Design microservices"
        assert resp.priority == "high"

    def test_default_priority(self) -> None:
        resp = Responsibility.model_validate({"description": "Write code"})
        assert resp.priority == "medium"

    def test_coerces_invalid_priority_to_medium(self) -> None:
        resp = Responsibility.model_validate({"description": "Test", "priority": "urgent"})
        assert resp.priority == "medium"

    def test_coerces_priority_case_insensitive(self) -> None:
        resp = Responsibility.model_validate({"description": "Test", "priority": "HIGH"})
        assert resp.priority == "high"

    def test_coerces_description_from_list(self) -> None:
        resp = Responsibility.model_validate({"description": ["design", "build"]})
        assert resp.description == "design; build"


class TestExperienceRequirement:
    def test_full_range(self) -> None:
        exp = ExperienceRequirement(min_years=3.0, max_years=5.0, domain="Backend")
        assert exp.min_years == 3.0
        assert exp.max_years == 5.0
        assert exp.domain == "Backend"

    def test_min_only(self) -> None:
        exp = ExperienceRequirement.model_validate({"min_years": 2, "max_years": None})
        assert exp.min_years == 2.0
        assert exp.max_years is None

    def test_coerces_string_years(self) -> None:
        exp = ExperienceRequirement.model_validate({"min_years": "3+", "max_years": "5"})
        assert exp.min_years == 3.0
        assert exp.max_years == 5.0

    def test_coerces_invalid_string_to_none(self) -> None:
        exp = ExperienceRequirement.model_validate({"min_years": "lots", "max_years": "many"})
        assert exp.min_years is None
        assert exp.max_years is None

    def test_defaults(self) -> None:
        exp = ExperienceRequirement.model_validate({})
        assert exp.min_years is None
        assert exp.max_years is None
        assert exp.domain == ""


class TestJobProfile:
    def test_full_profile(self) -> None:
        data = {
            "role": "Senior Backend Engineer",
            "seniority": "Senior",
            "must_have_skills": [
                {"name": "Python", "category": "Programming Language"},
                {"name": "FastAPI", "category": "Framework"},
            ],
            "preferred_skills": [
                {"name": "Kubernetes", "category": "DevOps"},
            ],
            "responsibilities": [
                {"description": "Design and build APIs", "priority": "high"},
                {"description": "Mentor junior developers", "priority": "medium"},
            ],
            "experience_required": {
                "min_years": 5,
                "max_years": 8,
                "domain": "Backend Development",
            },
        }
        profile = JobProfile.model_validate(data)
        assert profile.role == "Senior Backend Engineer"
        assert profile.seniority == "Senior"
        assert len(profile.must_have_skills) == 2
        assert profile.must_have_skills[0].name == "Python"
        assert len(profile.preferred_skills) == 1
        assert len(profile.responsibilities) == 2
        assert profile.responsibilities[0].priority == "high"
        assert profile.experience_required.min_years == 5.0
        assert profile.experience_required.domain == "Backend Development"

    def test_empty_profile(self) -> None:
        profile = JobProfile.model_validate({})
        assert profile.role == ""
        assert profile.seniority == ""
        assert profile.must_have_skills == []
        assert profile.preferred_skills == []
        assert profile.responsibilities == []
        assert profile.experience_required.min_years is None

    def test_ignores_extra_keys(self) -> None:
        data = {"role": "Engineer", "unknown": "ignored"}
        profile = JobProfile.model_validate(data)
        assert profile.role == "Engineer"

    def test_seniority_normalization_senior(self) -> None:
        profile = JobProfile.model_validate({"seniority": "senior"})
        assert profile.seniority == "Senior"

    def test_seniority_normalization_entry_to_junior(self) -> None:
        profile = JobProfile.model_validate({"seniority": "Entry"})
        assert profile.seniority == "Junior"

    def test_seniority_normalization_sr(self) -> None:
        profile = JobProfile.model_validate({"seniority": "Sr"})
        assert profile.seniority == "Senior"

    def test_seniority_normalization_vp(self) -> None:
        profile = JobProfile.model_validate({"seniority": "vp"})
        assert profile.seniority == "VP"

    def test_seniority_unknown_passes_through(self) -> None:
        profile = JobProfile.model_validate({"seniority": "Wizard"})
        assert profile.seniority == "Wizard"

    def test_seniority_empty_when_none(self) -> None:
        profile = JobProfile.model_validate({"seniority": None})
        assert profile.seniority == ""

    def test_role_coerces_list(self) -> None:
        profile = JobProfile.model_validate({"role": ["Backend", "Engineer"]})
        assert profile.role == "Backend; Engineer"
