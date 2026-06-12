type ApiErrorPayload = { detail?: string };

function getBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) throw new Error("NEXT_PUBLIC_API_URL is not defined.");
  return url;
}

export async function apiFetch<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(new URL(path, getBaseUrl()).toString(), init);

  if (!response.ok) {
    let detail = "Request failed.";
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default message
    }
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
