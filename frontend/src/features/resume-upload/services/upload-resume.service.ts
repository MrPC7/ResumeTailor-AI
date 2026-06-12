import type { UploadedResume } from "@/features/resume-upload/types/upload.types";

type ApiErrorPayload = {
  detail?: string;
};

export async function uploadResume(file: File): Promise<UploadedResume> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!baseUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is not defined.");
  }

  const uploadEndpoint = new URL("/api/upload", baseUrl);

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(uploadEndpoint.toString(), {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = "Failed to upload file.";

    try {
      const errorPayload = (await response.json()) as ApiErrorPayload;
      if (errorPayload.detail) {
        detail = errorPayload.detail;
      }
    } catch {
      detail = "Failed to upload file.";
    }

    throw new Error(detail);
  }

  return (await response.json()) as UploadedResume;
}
