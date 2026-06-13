import { z } from "zod";
import { jsonPost } from "@/features/workflow/services/api";
import type {
  AnalyzedJD,
  ATSAnalysisResult,
  ATSComparisonResult,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";

// ── Zod response schemas ──────────────────────────────────────────────────

const ATSScoresSchema = z.object({
  skills: z.number().int().min(0).max(100),
  keywords: z.number().int().min(0).max(100),
  experience: z.number().int().min(0).max(100),
  education: z.number().int().min(0).max(100),
});

const RecommendationGroupSchema = z.object({
  title: z.string(),
  items: z.array(z.string()),
});

const ATSAnalysisResultSchema = z.object({
  overallScore: z.number().int().min(0).max(100),
  scores: ATSScoresSchema,
  matchedKeywords: z.array(z.string()),
  missingKeywords: z.array(z.string()),
  recommendations: z.array(RecommendationGroupSchema),
});

const ATSComparisonResultSchema = z.object({
  beforeScore: z.number().int().min(0).max(100),
  afterScore: z.number().int().min(0).max(100),
  improvement: z.number().int(),
  before: ATSAnalysisResultSchema,
  after: ATSAnalysisResultSchema,
});

// ── Service functions ─────────────────────────────────────────────────────

export async function analyzeATS(
  resume: StructuredResume,
  jobDescription: AnalyzedJD,
): Promise<ATSAnalysisResult> {
  const raw = await jsonPost<unknown>("/api/ats/analyze", { resume, jobDescription });
  return ATSAnalysisResultSchema.parse(raw);
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
