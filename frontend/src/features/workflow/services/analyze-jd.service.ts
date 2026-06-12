import { jsonPost } from "@/features/workflow/services/api";
import type { AnalyzedJD } from "@/features/workflow/types/workflow.types";

export function analyzeJD(jobDescription: string): Promise<AnalyzedJD> {
  return jsonPost<AnalyzedJD>("/api/analyze-jd", { jobDescription });
}
