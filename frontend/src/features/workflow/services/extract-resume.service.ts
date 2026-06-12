import { jsonPost } from "@/features/workflow/services/api";
import type { StructuredResume } from "@/features/workflow/types/workflow.types";

export function extractResume(rawText: string): Promise<StructuredResume> {
  return jsonPost<StructuredResume>("/api/extract-resume", { rawText });
}
