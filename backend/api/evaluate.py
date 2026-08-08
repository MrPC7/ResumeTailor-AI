"""v2 evaluation endpoint — runs the full multi-agent pipeline."""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from core.config import limiter, settings
from schemas.evaluate import EvaluateJobResponse, EvaluateRequest, EvaluateResponse
from schemas.job import Job
from services.agents.resume_analyzer import resume_analyzer_agent
from services.agents.jd_analyzer import jd_analyzer_agent
from services.agents.recruiter import recruiter_agent
from services.job_manager import JobNotFoundError, job_manager
from services.orchestrator.evaluation_pipeline import (
    EvaluationPipeline,
)

router = APIRouter(tags=["evaluate"])

_pipeline = EvaluationPipeline(
    resume_analyzer=resume_analyzer_agent,
    jd_analyzer=jd_analyzer_agent,
    recruiter=recruiter_agent,
)


@router.post("/evaluate", response_model=EvaluateJobResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def evaluate(
    request: Request,
    body: EvaluateRequest,
    background_tasks: BackgroundTasks,
) -> EvaluateJobResponse:
    job = job_manager.create_job()
    background_tasks.add_task(
        _run_evaluation_job,
        job.job_id,
        body.raw_resume_text,
        body.raw_jd_text,
    )
    return EvaluateJobResponse(job_id=job.job_id)


@router.get("/evaluate/{job_id}", response_model=Job)
async def get_evaluation_job(job_id: str) -> Job:
    try:
        return job_manager.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        ) from exc


async def _run_evaluation_job(
    job_id: str,
    raw_resume_text: str,
    raw_jd_text: str,
) -> None:
    async def update_job_progress(progress: int, current_step: str) -> None:
        job_manager.update_progress(job_id, progress, current_step)

    job_manager.update_progress(job_id, progress=5, current_step="Initializing")
    try:
        result = await _pipeline.run(
            raw_resume_text=raw_resume_text,
            raw_jd_text=raw_jd_text,
            progress_callback=update_job_progress,
        )
    except Exception as exc:
        job_manager.fail_job(job_id, str(exc))
        return

    response = EvaluateResponse(
        candidate_profile=result.candidate_profile,
        job_profile=result.job_profile,
        evaluation=result.evaluation,
        suggestions=result.evaluation.suggestions,
    )
    job_manager.complete_job(job_id, response.model_dump(by_alias=True))
