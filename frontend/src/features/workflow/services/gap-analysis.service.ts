import { jsonPost } from "@/features/workflow/services/api";
import type {
  AnalyzedJD,
  GapAnalysis,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";

export function fetchGapAnalysis(resume: StructuredResume, jd: AnalyzedJD): Promise<GapAnalysis> {
  return jsonPost<GapAnalysis>("/api/gap-analysis", { resume, jd });
}
