import { jsonPost } from "@/features/workflow/services/api";
import type {
  AnalyzedJD,
  StructuredResume,
  SuggestionsStepData,
} from "@/features/workflow/types/workflow.types";

type CustomizeResumeResponse = {
  customizedResume: StructuredResume;
  suggestions: string[];
  compressed: boolean;
};

export function customizeResume(
  resume: StructuredResume,
  jd: AnalyzedJD,
  selectedSuggestionIds: string[],
  suggestions: SuggestionsStepData["suggestions"]
): Promise<CustomizeResumeResponse> {
  return jsonPost<CustomizeResumeResponse>("/api/customize-resume", {
    resume,
    jd,
    selectedSuggestionIds,
    suggestions,
  });
}
