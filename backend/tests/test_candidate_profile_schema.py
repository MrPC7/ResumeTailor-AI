"""Unit tests for the CandidateProfile schema (agent_models)."""
from __future__ import annotations

import pytest
from schemas.agent_models import (
    CandidateProfile,
    Certification,
    Education,
    Project,
    Skill,
    WorkExperience,
)


class TestSkillModel:
    def test_valid_skill(self) -> None:
        skill = Skill(name="Python", category="Programming Language")
        assert skill.name == "Python"
        assert skill.category == "Programming Language"

    def test_coerces_list_to_string(self) -> None:
        skill = Skill.model_validate({"name": ["Python", "3.11"], "category": "Language"})
        assert skill.name == "Python; 3.11"

    def test_coerces_dict_to_string(self) -> None:
        skill = Skill.model_validate({"name": {"lang": "Python"}, "category": "PL"})
        assert skill.name == "lang: Python"

    def test_coerces_none_to_empty(self) -> None:
        skill = Skill.model_validate({"name": None, "category": None})
        assert skill.name == ""
        assert skill.category == ""

    def test_defaults_to_empty_strings(self) -> None:
        skill = Skill.model_validate({})
        assert skill.name == ""
        assert skill.category == ""

    def test_ignores_extra_fields(self) -> None:
        skill = Skill.model_validate({"name": "Go", "category": "PL", "extra": True})
        assert skill.name == "Go"


class TestWorkExperience:
    def test_valid_experience(self) -> None:
        exp = WorkExperience(
            company="Acme",
            position="Engineer",
            duration="2020 - 2023",
            responsibilities=["Built APIs", "Led team"],
            technologies=["Python", "FastAPI"],
        )
        assert exp.company == "Acme"
        assert len(exp.responsibilities) == 2
        assert "FastAPI" in exp.technologies

    def test_defaults(self) -> None:
        exp = WorkExperience.model_validate({})
        assert exp.company == ""
        assert exp.responsibilities == []
        assert exp.technologies == []

    def test_coercion(self) -> None:
        exp = WorkExperience.model_validate({"company": ["Acme", "Inc"], "position": 123})
        assert exp.company == "Acme; Inc"
        assert exp.position == "123"


class TestEducation:
    def test_valid_education(self) -> None:
        edu = Education(
            institution="MIT",
            degree="B.S.",
            field_of_study="Computer Science",
            year="2020",
        )
        assert edu.institution == "MIT"
        assert edu.field_of_study == "Computer Science"

    def test_defaults(self) -> None:
        edu = Education.model_validate({})
        assert edu.institution == ""
        assert edu.field_of_study == ""


class TestProject:
    def test_valid_project(self) -> None:
        proj = Project(
            name="TaskApp",
            description="A task manager",
            technologies=["React", "Node"],
            role="Lead developer",
        )
        assert proj.name == "TaskApp"
        assert "React" in proj.technologies
        assert proj.role == "Lead developer"

    def test_defaults(self) -> None:
        proj = Project.model_validate({})
        assert proj.technologies == []
        assert proj.role == ""


class TestCertification:
    def test_valid_certification(self) -> None:
        cert = Certification(name="AWS SAA", issuer="Amazon", year="2023")
        assert cert.name == "AWS SAA"

    def test_coercion(self) -> None:
        cert = Certification.model_validate({"name": None, "issuer": None, "year": None})
        assert cert.name == ""


class TestCandidateProfile:
    def test_full_profile(self) -> None:
        data = {
            "skills": [
                {"name": "Python", "category": "Programming Language"},
                {"name": "AWS", "category": "Cloud"},
            ],
            "work_experience": [
                {
                    "company": "Acme Corp",
                    "position": "Senior Engineer",
                    "duration": "2021 - Present",
                    "responsibilities": ["Built microservices", "Mentored juniors"],
                    "technologies": ["Python", "Docker"],
                }
            ],
            "education": [
                {
                    "institution": "IIT Delhi",
                    "degree": "B.Tech",
                    "field_of_study": "Computer Science",
                    "year": "2018",
                }
            ],
            "projects": [
                {
                    "name": "ResumeTailor",
                    "description": "AI resume builder",
                    "technologies": ["FastAPI", "React"],
                    "role": "Full-stack developer",
                }
            ],
            "certifications": [
                {"name": "AWS SAA", "issuer": "Amazon", "year": "2022"}
            ],
            "total_years_experience": 4.5,
            "primary_domain": "Backend Development",
        }
        profile = CandidateProfile.model_validate(data)
        assert len(profile.skills) == 2
        assert profile.skills[0].name == "Python"
        assert len(profile.work_experience) == 1
        assert profile.work_experience[0].company == "Acme Corp"
        assert len(profile.education) == 1
        assert len(profile.projects) == 1
        assert len(profile.certifications) == 1
        assert profile.total_years_experience == 4.5
        assert profile.primary_domain == "Backend Development"

    def test_empty_profile(self) -> None:
        profile = CandidateProfile.model_validate({})
        assert profile.skills == []
        assert profile.work_experience == []
        assert profile.education == []
        assert profile.projects == []
        assert profile.certifications == []
        assert profile.total_years_experience is None
        assert profile.primary_domain == ""

    def test_ignores_extra_keys(self) -> None:
        data = {"skills": [], "unknown_field": "should be ignored"}
        profile = CandidateProfile.model_validate(data)
        assert profile.skills == []

    def test_coerces_primary_domain(self) -> None:
        data = {"primary_domain": ["Backend", "DevOps"]}
        profile = CandidateProfile.model_validate(data)
        assert profile.primary_domain == "Backend; DevOps"

    def test_null_years_experience(self) -> None:
        data = {"total_years_experience": None}
        profile = CandidateProfile.model_validate(data)
        assert profile.total_years_experience is None
