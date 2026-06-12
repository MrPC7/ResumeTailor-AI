from __future__ import annotations

import re

from fastapi import UploadFile

from core.config import settings
from services.resume_parser.parser_factory import resume_parser_factory


class ResumeParseValidationError(Exception):
    pass


class ResumeParseService:
    def __init__(self, max_size_bytes: int) -> None:
        self.max_size_bytes = max_size_bytes

    @staticmethod
    def _clean_text(text: str) -> str:
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        non_empty_lines = [line for line in lines if line]
        return "\n".join(non_empty_lines)

    async def parse_resume(self, file: UploadFile) -> str:
        extension = resume_parser_factory.validate_file_metadata(file.filename, file.content_type)

        try:
            file_bytes = await file.read()
        except Exception as exc:
            raise ResumeParseValidationError("Unable to read uploaded file.") from exc
        finally:
            await file.close()

        if not file_bytes:
            raise ResumeParseValidationError("Uploaded file is empty.")

        if len(file_bytes) > self.max_size_bytes:
            raise ResumeParseValidationError("File size exceeds 10MB limit.")

        strategy = resume_parser_factory.get_strategy(extension)

        try:
            raw_text = strategy.parse(file_bytes)
        except ValueError as exc:
            raise ResumeParseValidationError(str(exc)) from exc

        cleaned_text = self._clean_text(raw_text)
        if not cleaned_text:
            raise ResumeParseValidationError("No readable text found in resume.")

        return cleaned_text


resume_parse_service = ResumeParseService(max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES)
