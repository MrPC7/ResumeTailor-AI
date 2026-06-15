import { getBaseUrl } from "@/features/workflow/services/api";
import type { StructuredResume } from "@/features/workflow/types/workflow.types";
import { pushToast } from "@/lib/toast";

export type ExportFormat = "pdf" | "docx";

export type ExportPayload = {
  resume: StructuredResume;
  format: ExportFormat;
  fileName?: string;
};

type ExportErrorPayload = {
  detail?: string;
  error?: {
    code?: string;
    message?: string;
  };
};

const EXPORT_TIMEOUT_MS = 60_000;

function getDownloadFileName(contentDisposition: string | null, fallback: string): string {
  if (!contentDisposition) return fallback;

  const match = contentDisposition.match(/filename="?([^";]+)"?/i);
  if (!match?.[1]) return fallback;

  return match[1];
}

export async function exportResume(
  payload: ExportPayload
): Promise<{ blob: Blob; fileName: string }> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), EXPORT_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(new URL("/api/export", getBaseUrl()).toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
  } catch (error) {
    const message =
      error instanceof DOMException && error.name === "AbortError"
        ? "Export request timed out. Please try again."
        : "Network error while exporting. Please try again.";
    pushToast({ type: "error", message });
    throw new Error(message);
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let detail = "Failed to export resume.";
    try {
      const body = (await response.json()) as ExportErrorPayload;
      detail = body.error?.message ?? body.detail ?? detail;
    } catch {
      // Keep default message.
    }
    pushToast({ type: "error", message: detail });
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
