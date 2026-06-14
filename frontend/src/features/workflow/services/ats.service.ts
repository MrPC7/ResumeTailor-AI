import { z } from "zod";
import { jsonPost } from "@/features/workflow/services/api";
import type {
  AnalyzedJD,
  ATSEvaluationResult,
  ATSComparisonResult,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";

// ── Zod response schemas ──────────────────────────────────────────────────

const ATSScoresSchema = z.object({
  skills: z.number().int().min(0).max(100),
  keywords: z.number().int().min(0).max(100),
  experience: z.number().int().min(0).max(100),
  education: z.number().int().min(0).max(100),
  overallFit: z.number().int().min(0).max(100),
});

const ATSEvaluationResultSchema = z.object({
  overallScore: z.number().int().min(0).max(100),
  confidence: z.number().int().min(0).max(100),
  scores: ATSScoresSchema,
  strengths: z.array(z.string()),
  weaknesses: z.array(z.string()),
  missingKeywords: z.array(z.string()),
  recommendedActions: z.array(z.string()),
});

const ATSComparisonResultSchema = z.object({
  beforeScore: z.number().int().min(0).max(100),
  afterScore: z.number().int().min(0).max(100),
  improvement: z.number().int(),
  before: ATSEvaluationResultSchema,
  after: ATSEvaluationResultSchema,
});

// ── Service functions ─────────────────────────────────────────────────────

export async function analyzeATS(
  resume: StructuredResume,
  jobDescription: AnalyzedJD,
): Promise<ATSEvaluationResult> {
  const raw = await jsonPost<unknown>("/api/ats/analyze", { resume, jobDescription });
  return ATSEvaluationResultSchema.parse(raw);
}

export async function compareATS(
  originalResume: StructuredResume,
  customizedResume: StructuredResume,
  jobDescription: AnalyzedJD,
): Promise<ATSComparisonResult> {
  const raw = await jsonPost<unknown>("/api/ats/compare", {
    originalResume,
    customizedResume,
    jobDescription,
  });
  return ATSComparisonResultSchema.parse(raw);
}
