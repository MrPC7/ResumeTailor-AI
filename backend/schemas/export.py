from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from schemas.extract_resume import ExtractResumeResponse


class ExportFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


class ExportResumeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resume: ExtractResumeResponse
    format: ExportFormat
    file_name: str | None = Field(default=None, alias="fileName", min_length=1, max_length=120)
