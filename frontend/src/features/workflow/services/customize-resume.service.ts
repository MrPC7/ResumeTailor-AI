import { jsonPost } from "@/features/workflow/services/api";
import type {
  AnalyzedJD,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";

type CustomizeResumeResponse = {
  customizedResume: StructuredResume;
  suggestions: string[];
};

export function customizeResume(
  resume: StructuredResume,
  jd: AnalyzedJD,
  acceptedRecommendations: string[],
  rejectedRecommendations: string[],
): Promise<CustomizeResumeResponse> {
  return jsonPost<CustomizeResumeResponse>("/api/customize-resume", {
    resume,
    jd,
    acceptedRecommendations,
    rejectedRecommendations,
  });
}
