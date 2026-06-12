import { multipartPost } from "@/features/workflow/services/api";

type ParseResumeResponse = { rawText: string };

export function parseResume(file: File): Promise<ParseResumeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return multipartPost<ParseResumeResponse>("/api/parse-resume", formData);
}
