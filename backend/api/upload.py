from fastapi import APIRouter, File, HTTPException, UploadFile, status

from schemas.upload import UploadResponse
from services.upload_service import UploadValidationError, upload_service

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)) -> UploadResponse:
    try:
        return await upload_service.save_temporary_file(file)
    except UploadValidationError as exc:
        error_text = str(exc).lower()
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if "exceeds" in error_text or "too large" in error_text
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process file upload.",
        ) from exc
