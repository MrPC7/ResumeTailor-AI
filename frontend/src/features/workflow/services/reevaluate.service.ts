import type { ReevaluationResult } from "@/components/recruiter/types";
import { jsonPost } from "./api";

export function runReevaluation(
  originalResumeText: string,
  optimizedResumeText: string,
  rawJdText: string
): Promise<ReevaluationResult> {
  return jsonPost<ReevaluationResult>("/api/reevaluate", {
    originalResumeText,
    optimizedResumeText,
    rawJdText,
  });
}
