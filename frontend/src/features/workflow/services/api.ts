import { pushToast } from "@/lib/toast";

type ApiErrorPayload = {
  detail?: string;
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
};

const REQUEST_TIMEOUT_MS = 45_000;

function parseApiError(payload: ApiErrorPayload | null, fallback: string): string {
  if (!payload) return fallback;
  if (payload.error?.message) return payload.error.message;
  if (payload.detail) return payload.detail;
  return fallback;
}

async function safeReadErrorBody(response: Response): Promise<ApiErrorPayload | null> {
  try {
    return (await response.json()) as ApiErrorPayload;
  } catch {
    return null;
  }
}

export function getBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) throw new Error("NEXT_PUBLIC_API_URL is not defined.");
  return url;
}

export async function apiFetch<T>(path: string, init: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(new URL(path, getBaseUrl()).toString(), {
      ...init,
      signal: controller.signal,
    });
  } catch (error) {
    const message =
      error instanceof DOMException && error.name === "AbortError"
        ? "Request timed out. Please try again."
        : "Network error. Please check your internet connection and try again.";
    pushToast({ type: "error", message });
    throw new Error(message);
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!response.ok) {
    const payload = await safeReadErrorBody(response);
    const detail = parseApiError(payload, "Request failed.");
    pushToast({ type: "error", message: detail });
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function jsonPost<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function multipartPost<T>(path: string, formData: FormData): Promise<T> {
  return apiFetch<T>(path, { method: "POST", body: formData });
}
