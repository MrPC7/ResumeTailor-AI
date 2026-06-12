from __future__ import annotations

import fitz


class PDFParser:
    def parse(self, file_bytes: bytes) -> str:
        try:
            with fitz.open(stream=file_bytes, filetype="pdf") as document:
                pages_text = [page.get_text("text") for page in document]
        except Exception as exc:
            raise ValueError("Failed to parse PDF file.") from exc

        return "\n".join(pages_text)
