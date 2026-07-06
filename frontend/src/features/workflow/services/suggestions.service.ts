import type { SuggestionReport } from "@/components/suggestions/types";
import type { RecruiterStepData } from "@/features/workflow/types/workflow.types";
import { jsonPost } from "./api";

type SuggestionsApiResponse = {
  suggestions: SuggestionReport;
};

export function fetchSuggestions(data: RecruiterStepData): Promise<SuggestionsApiResponse> {
  return jsonPost<SuggestionsApiResponse>("/api/suggestions", {
    candidateProfile: data.candidateProfile,
    jobProfile: data.jobProfile,
    evaluation: data.evaluation,
  });
}
