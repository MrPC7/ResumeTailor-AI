"""ATS Engine — orchestrates keyword matching, scoring, and recommendations."""
from __future__ import annotations

from schemas.analyze_jd import AnalyzeJDResponse
from schemas.extract_resume import ExtractResumeResponse
from services.ats.keyword_matcher import build_resume_term_set
from services.ats.models import ATSAnalysisResult, ATSComparisonResult, ATSScores
from services.ats.recommendation_engine import generate_recommendations
from services.ats.score_calculator import (
    build_keyword_split,
    compute_education_score,
    compute_experience_score,
    compute_keyword_score,
    compute_overall_score,
    compute_skills_score,
)


class ATSEngineError(Exception):
    """Raised when analysis cannot be completed."""


class ATSEngine:
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        resume: ExtractResumeResponse,
        jd: AnalyzeJDResponse,
    ) -> ATSAnalysisResult:
        try:
            return self._run_analysis(resume, jd)
        except ATSEngineError:
            raise
        except Exception as exc:
            raise ATSEngineError("ATS analysis failed.") from exc

    def compare(
        self,
        original: ExtractResumeResponse,
        customized: ExtractResumeResponse,
        jd: AnalyzeJDResponse,
    ) -> ATSComparisonResult:
        try:
            before = self._run_analysis(original, jd)
            after = self._run_analysis(customized, jd)
            improvement = after.overallScore - before.overallScore
            return ATSComparisonResult(
                beforeScore=before.overallScore,
                afterScore=after.overallScore,
                improvement=improvement,
                before=before,
                after=after,
            )
        except ATSEngineError:
            raise
        except Exception as exc:
            raise ATSEngineError("ATS comparison failed.") from exc

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _build_text_blocks(resume: ExtractResumeResponse) -> list[str]:
        blocks: list[str] = []
        if resume.summary:
            blocks.append(resume.summary)
        for exp in resume.experience:
            blocks.extend(
                filter(None, [exp.position, exp.company, exp.description])
            )
        for edu in resume.education:
            blocks.extend(filter(None, [edu.degree, edu.institution]))
        for proj in resume.projects:
            blocks.extend(filter(None, [proj.name, proj.description]))
            blocks.extend(proj.technologies)
        return blocks

    def _run_analysis(
        self,
        resume: ExtractResumeResponse,
        jd: AnalyzeJDResponse,
    ) -> ATSAnalysisResult:
        text_blocks = self._build_text_blocks(resume)
        full_phrases, token_pool = build_resume_term_set(resume.skills, text_blocks)

        skills_score = compute_skills_score(resume, jd, full_phrases, token_pool)
        keyword_score = compute_keyword_score(jd, full_phrases, token_pool)
        experience_score = compute_experience_score(resume, jd)
        education_score = compute_education_score(resume)
        overall_score = compute_overall_score(
            skills_score, keyword_score, experience_score, education_score
        )

        matched, missing = build_keyword_split(jd, full_phrases, token_pool)

        recommendations = generate_recommendations(
            resume,
            jd,
            missing,
            skills_score,
            keyword_score,
            experience_score,
            education_score,
        )

        return ATSAnalysisResult(
            overallScore=overall_score,
            scores=ATSScores(
                skills=skills_score,
                keywords=keyword_score,
                experience=experience_score,
                education=education_score,
            ),
            matchedKeywords=matched,
            missingKeywords=missing,
            recommendations=recommendations,
        )
