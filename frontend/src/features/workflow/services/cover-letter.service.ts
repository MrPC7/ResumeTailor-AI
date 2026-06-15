import { z } from "zod";
import { jsonPost } from "@/features/workflow/services/api";
import type {
  AnalyzedJD,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";

const CoverLetterResponseSchema = z.object({
  coverLetter: z.string(),
  strengthsHighlighted: z.array(z.string()),
  matchingSkillsUsed: z.array(z.string()),
});

export type CoverLetterResult = z.infer<typeof CoverLetterResponseSchema>;

export async function generateCoverLetter(
  resume: StructuredResume,
  jd: AnalyzedJD,
): Promise<CoverLetterResult> {
  const raw = await jsonPost<unknown>("/api/cover-letter", { resume, jd });
  return CoverLetterResponseSchema.parse(raw);
}
