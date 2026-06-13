from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO

import fitz
from docx import Document

from schemas.extract_resume import ExtractResumeResponse
from schemas.export import ExportFormat


class ResumeExportError(Exception):
    """Raised when export generation fails."""


@dataclass(frozen=True)
class ExportFile:
    content: bytes
    media_type: str
    extension: str


class ResumeExporter:
    def export(self, resume: ExtractResumeResponse, export_format: ExportFormat) -> ExportFile:
        if export_format == ExportFormat.PDF:
            return ExportFile(
                content=self._build_pdf(resume),
                media_type="application/pdf",
                extension="pdf",
            )

        if export_format == ExportFormat.DOCX:
            return ExportFile(
                content=self._build_docx(resume),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                extension="docx",
            )

        raise ResumeExportError("Unsupported export format.")

    @staticmethod
    def build_file_base_name(resume_name: str | None, requested_name: str | None) -> str:
        raw_name = (requested_name or resume_name or "resume").strip()
        sanitized = re.sub(r"[^A-Za-z0-9_-]", "_", raw_name)
        normalized = re.sub(r"_+", "_", sanitized).strip("_")
        return normalized or "resume"

    @staticmethod
    def _build_pdf(resume: ExtractResumeResponse) -> bytes:
        lines = ResumeExporter._compose_plain_text_lines(resume)

        document = fitz.open()
        try:
            page = document.new_page()
            y = 48.0
            left = 48.0
            bottom_limit = page.rect.height - 48.0
            line_height = 14.0

            for line in lines:
                if y + line_height > bottom_limit:
                    page = document.new_page()
                    y = 48.0

                text = line if line else " "
                page.insert_text((left, y), text, fontsize=11)
                y += line_height

            return document.tobytes(garbage=4, deflate=True)
        except Exception as exc:
            raise ResumeExportError("Unable to generate PDF file.") from exc
        finally:
            document.close()

    @staticmethod
    def _build_docx(resume: ExtractResumeResponse) -> bytes:
        try:
            document = Document()
            document.add_heading(resume.name or "Customized Resume", level=0)

            if resume.email or resume.phone:
                contact_parts = [part for part in [resume.email, resume.phone] if part]
                document.add_paragraph(" | ".join(contact_parts))

            if resume.summary:
                document.add_heading("Summary", level=1)
                document.add_paragraph(resume.summary)

            if resume.skills:
                document.add_heading("Skills", level=1)
                document.add_paragraph(", ".join(skill.strip() for skill in resume.skills if skill.strip()))

            if resume.experience:
                document.add_heading("Experience", level=1)
                for item in resume.experience:
                    header = " - ".join(part for part in [item.position, item.company] if part)
                    if header:
                        document.add_paragraph(header)
                    if item.duration:
                        document.add_paragraph(item.duration)
                    if item.description:
                        document.add_paragraph(item.description)

            if resume.education:
                document.add_heading("Education", level=1)
                for item in resume.education:
                    edu_line = ", ".join(
                        part for part in [item.degree, item.institution, item.year] if part
                    )
                    if edu_line:
                        document.add_paragraph(edu_line)

            if resume.projects:
                document.add_heading("Projects", level=1)
                for item in resume.projects:
                    if item.name:
                        document.add_paragraph(item.name)
                    if item.description:
                        document.add_paragraph(item.description)
                    if item.technologies:
                        tech_line = ", ".join(
                            tech.strip() for tech in item.technologies if tech.strip()
                        )
                        if tech_line:
                            document.add_paragraph(f"Technologies: {tech_line}")

            stream = BytesIO()
            document.save(stream)
            return stream.getvalue()
        except Exception as exc:
            raise ResumeExportError("Unable to generate DOCX file.") from exc

    @staticmethod
    def _compose_plain_text_lines(resume: ExtractResumeResponse) -> list[str]:
        lines: list[str] = []

        lines.append(resume.name or "Customized Resume")

        contact_parts = [part for part in [resume.email, resume.phone] if part]
        if contact_parts:
            lines.append(" | ".join(contact_parts))

        if resume.summary:
            lines.extend(["", "Summary", resume.summary])

        if resume.skills:
            lines.extend(["", "Skills", ", ".join(skill for skill in resume.skills if skill)])

        if resume.experience:
            lines.append("")
            lines.append("Experience")
            for item in resume.experience:
                header = " - ".join(part for part in [item.position, item.company] if part)
                if header:
                    lines.append(header)
                if item.duration:
                    lines.append(item.duration)
                if item.description:
                    lines.append(item.description)
                lines.append("")

        if resume.education:
            lines.append("Education")
            for item in resume.education:
                edu_line = ", ".join(part for part in [item.degree, item.institution, item.year] if part)
                if edu_line:
                    lines.append(edu_line)

        if resume.projects:
            lines.append("")
            lines.append("Projects")
            for item in resume.projects:
                if item.name:
                    lines.append(item.name)
                if item.description:
                    lines.append(item.description)
                if item.technologies:
                    tech_line = ", ".join(tech for tech in item.technologies if tech)
                    if tech_line:
                        lines.append(f"Technologies: {tech_line}")
                lines.append("")

        return lines


resume_exporter = ResumeExporter()
