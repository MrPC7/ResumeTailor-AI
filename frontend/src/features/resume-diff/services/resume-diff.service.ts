import type { ResumeDiffResponse } from "@/features/resume-diff/types/diff.types";

type ApiErrorPayload = {
  detail?: string;
};

export async function fetchResumeDiff(
  original: object,
  customized: object
): Promise<ResumeDiffResponse> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!baseUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is not defined.");
  }

  const endpoint = new URL("/api/resume-diff", baseUrl);

  const response = await fetch(endpoint.toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ original, customized }),
  });

  if (!response.ok) {
    let detail = "Failed to compute resume diff.";
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (payload.detail) detail = payload.detail;
    } catch {
      detail = "Failed to compute resume diff.";
    }
    throw new Error(detail);
  }

  return (await response.json()) as ResumeDiffResponse;
}
