"""Unit tests for TailoredResume schema."""
from __future__ import annotations

import pytest
from schemas.agent_models import TailoredResume, TailoredExperience, TailoredProject


class TestTailoredExperience:
    def test_valid_experience(self) -> None:
        exp = TailoredExperience(
            company="Acme",
            position="Engineer",
            duration="2021 - Present",
            description="Built scalable APIs",
            technologies=["Python", "FastAPI"],
        )
        assert exp.company == "Acme"
        assert exp.description == "Built scalable APIs"
        assert len(exp.technologies) == 2

    def test_defaults(self) -> None:
        exp = TailoredExperience.model_validate({})
        assert exp.company == ""
        assert exp.description == ""
        assert exp.technologies == []

    def test_coercion(self) -> None:
        exp = TailoredExperience.model_validate({
            "company": ["Acme", "Inc"],
            "position": None,
        })
        assert exp.company == "Acme; Inc"
        assert exp.position == ""


class TestTailoredProject:
    def test_valid_project(self) -> None:
        proj = TailoredProject(
            name="TaskAPI",
            description="REST task manager optimized for performance",
            technologies=["FastAPI", "PostgreSQL"],
        )
        assert proj.name == "TaskAPI"
        assert "optimized" in proj.description

    def test_defaults(self) -> None:
        proj = TailoredProject.model_validate({})
        assert proj.name == ""
        assert proj.technologies == []


class TestTailoredResume:
    def test_full_tailored_resume(self) -> None:
        data = {
            "summary": "Senior Backend Engineer with 5 years experience",
            "skills": ["Python", "FastAPI", "Docker", "AWS"],
            "experience": [
                {
                    "company": "Acme Corp",
                    "position": "Senior Engineer",
                    "duration": "2021 - Present",
                    "description": "Built microservices with FastAPI and Docker",
                    "technologies": ["Python", "FastAPI", "Docker"],
                }
            ],
            "projects": [
                {
                    "name": "ResumeTailor",
                    "description": "AI resume builder with FastAPI backend",
                    "technologies": ["FastAPI", "React"],
                }
            ],
            "improvements_made": [
                "Reordered skills to prioritize must-have requirements",
                "Rewrote summary targeting Senior Backend role",
            ],
            "gaps_addressed": [
                "Surfaced Docker experience to address DevOps gap",
            ],
        }
        resume = TailoredResume.model_validate(data)
        assert "Senior Backend" in resume.summary
        assert len(resume.skills) == 4
        assert resume.skills[0] == "Python"
        assert len(resume.experience) == 1
        assert resume.experience[0].company == "Acme Corp"
        assert len(resume.projects) == 1
        assert len(resume.improvements_made) == 2
        assert len(resume.gaps_addressed) == 1

    def test_empty_resume_defaults(self) -> None:
        resume = TailoredResume.model_validate({})
        assert resume.summary == ""
        assert resume.skills == []
        assert resume.experience == []
        assert resume.projects == []
        assert resume.improvements_made == []
        assert resume.gaps_addressed == []

    def test_ignores_extra_keys(self) -> None:
        data = {"summary": "Test", "unknown_field": "ignored"}
        resume = TailoredResume.model_validate(data)
        assert resume.summary == "Test"

    def test_summary_coerces_list(self) -> None:
        data = {"summary": ["Senior", "Engineer"]}
        resume = TailoredResume.model_validate(data)
        assert resume.summary == "Senior; Engineer"
