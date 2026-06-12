from __future__ import annotations

from pathlib import Path
from typing import Protocol

from services.resume_parser.docx_parser import DOCXParser
from services.resume_parser.pdf_parser import PDFParser

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class ParserStrategy(Protocol):
    def parse(self, file_bytes: bytes) -> str:
        ...


class ResumeParserFactory:
    def __init__(self) -> None:
        self._strategies: dict[str, ParserStrategy] = {
            ".pdf": PDFParser(),
            ".docx": DOCXParser(),
        }

    @staticmethod
    def validate_file_metadata(filename: str | None, content_type: str | None) -> str:
        if not filename:
            raise ValueError("File name is missing.")

        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported file extension. Use PDF or DOCX.")

        if not content_type or content_type not in SUPPORTED_CONTENT_TYPES:
            raise ValueError("Unsupported content type. Use PDF or DOCX.")

        return extension

    def get_strategy(self, extension: str) -> ParserStrategy:
        strategy = self._strategies.get(extension)
        if strategy is None:
            raise ValueError("No parser available for the file type.")
        return strategy


resume_parser_factory = ResumeParserFactory()
