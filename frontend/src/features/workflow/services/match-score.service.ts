import { jsonPost } from "@/features/workflow/services/api";
import type {
  AnalyzedJD,
  MatchScore,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";

export function fetchMatchScore(resume: StructuredResume, jd: AnalyzedJD): Promise<MatchScore> {
  return jsonPost<MatchScore>("/api/match-score", { resume, jd });
}
