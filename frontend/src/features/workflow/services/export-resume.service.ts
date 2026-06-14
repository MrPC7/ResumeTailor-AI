import { getBaseUrl } from "@/features/workflow/services/api";
import type { StructuredResume } from "@/features/workflow/types/workflow.types";

export type ExportFormat = "pdf" | "docx";

export type ExportPayload = {
  resume: StructuredResume;
  format: ExportFormat;
  fileName?: string;
};

function getDownloadFileName(contentDisposition: string | null, fallback: string): string {
  if (!contentDisposition) return fallback;

  const match = contentDisposition.match(/filename="?([^";]+)"?/i);
  if (!match?.[1]) return fallback;

  return match[1];
}

export async function exportResume(
  payload: ExportPayload
): Promise<{ blob: Blob; fileName: string }> {
  const response = await fetch(new URL("/api/export", getBaseUrl()).toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let detail = "Failed to export resume.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep default message.
    }
    throw new Error(detail);
  }

  const blob = await response.blob();
  const fileName = getDownloadFileName(
    response.headers.get("content-disposition"),
    `resume_customized.${payload.format}`
  );

  return { blob, fileName };
}

export function downloadBlob(blob: Blob, fileName: string): void {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}
