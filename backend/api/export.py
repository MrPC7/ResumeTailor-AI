from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from schemas.export import ExportFormat, ExportResumeRequest
from services.export_service import ResumeExportError, resume_exporter
from services.resume_customizer.length_guard import compress_resume, estimate_pdf_overflow
from services.llm import llm_client

router = APIRouter()


@router.post("/export")
async def export_resume(body: ExportResumeRequest) -> StreamingResponse:
    try:
        resume = body.resume

        # PDF overflow guard: compress content if it risks overflowing A4.
        if body.format == ExportFormat.PDF and estimate_pdf_overflow(resume):
            resume = await compress_resume(llm_client, resume)

        export_file = resume_exporter.export(resume, body.format)
        base_name = resume_exporter.build_file_base_name(body.resume.name, body.file_name)
        file_name = f"{base_name}_customized.{export_file.extension}"

        headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
        return StreamingResponse(
            BytesIO(export_file.content),
            media_type=export_file.media_type,
            headers=headers,
        )
    except ResumeExportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to export resume file.",
        ) from exc
