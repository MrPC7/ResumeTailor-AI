from __future__ import annotations

from io import BytesIO

from docx import Document


class DOCXParser:
    def parse(self, file_bytes: bytes) -> str:
        try:
            document = Document(BytesIO(file_bytes))
            paragraphs = [paragraph.text for paragraph in document.paragraphs]
        except Exception as exc:
            raise ValueError("Failed to parse DOCX file.") from exc

        return "\n".join(paragraphs)
