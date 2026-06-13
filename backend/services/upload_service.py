from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from core.config import settings
from schemas.upload import UploadResponse

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class UploadValidationError(Exception):
    pass


class UploadService:
    def __init__(self, upload_dir: str, max_size_bytes: int) -> None:
        self.upload_dir = Path(upload_dir)
        self.max_size_bytes = max_size_bytes
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_filename(filename: str | None) -> str:
        if not filename:
            raise UploadValidationError("File name is missing.")

        # Strip directory components to prevent path traversal.
        name = Path(filename).name
        if not name or name.startswith("."):
            raise UploadValidationError("Invalid file name.")

        extension = Path(name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise UploadValidationError("Unsupported file extension. Use PDF or DOCX.")

        return name

    @staticmethod
    def _validate_content_type(content_type: str | None) -> str:
        if not content_type or content_type not in ALLOWED_CONTENT_TYPES:
            raise UploadValidationError("Unsupported content type. Use PDF or DOCX.")
        return content_type

    async def save_temporary_file(self, file: UploadFile) -> UploadResponse:
        original_name = self._validate_filename(file.filename)
        content_type = self._validate_content_type(file.content_type)

        extension = Path(original_name).suffix.lower()
        generated_name = f"{uuid4().hex}{extension}"
        destination = self.upload_dir / generated_name

        file_size = 0

        try:
            with destination.open("wb") as output_file:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break

                    file_size += len(chunk)
                    if file_size > self.max_size_bytes:
                        raise UploadValidationError("File size exceeds 10MB limit.")

                    output_file.write(chunk)
        except UploadValidationError:
            if destination.exists():
                destination.unlink()
            raise
        finally:
            await file.close()

        return UploadResponse(
            file_name=original_name,
            file_size=file_size,
            file_type=content_type,
        )


upload_service = UploadService(
    upload_dir=settings.TEMP_UPLOAD_DIR,
    max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
)
