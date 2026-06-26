import type { EvaluateResponse } from "@/components/recruiter/types";
import { jsonPost } from "./api";

export function runEvaluation(rawResumeText: string, rawJdText: string): Promise<EvaluateResponse> {
  return jsonPost<EvaluateResponse>("/api/evaluate", {
    rawResumeText,
    rawJdText,
  });
}
