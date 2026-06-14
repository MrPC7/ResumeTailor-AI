import { z } from "zod";
import { jsonPost } from "@/features/workflow/services/api";
import type {
  AnalyzedJD,
  ATSEvaluationResult,
  ATSComparisonResult,
  PotentialScoreResult,
  RecommendationReport,
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

const PotentialScoreResultSchema = z.object({
  currentScore: z.number().int().min(0).max(100),
  potentialScore: z.number().int().min(0).max(100),
  improvementPotential: z.number().int().min(0),
});

const ImpactLevelSchema = z.enum(["critical", "high", "medium", "low"]);

const RecommendationSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  impactLevel: ImpactLevelSchema,
  estimatedPoints: z.number().int().min(0),
});

const RecommendationGroupSchema = z.object({
  groupId: z.string(),
  groupTitle: z.string(),
  recommendations: z.array(RecommendationSchema),
});

const RecommendationReportSchema = z.object({
  totalEstimatedGain: z.number().int().min(0),
  groups: z.array(RecommendationGroupSchema),
});

// ── Service functions ─────────────────────────────────────────────────────

export async function analyzeATS(
  resume: StructuredResume,
  jobDescription: AnalyzedJD,
): Promise<ATSEvaluationResult> {
  const raw = await jsonPost<unknown>("/api/ats/analyze", { resume, jobDescription });
  return ATSEvaluationResultSchema.parse(raw);
}

export async function predictPotentialScore(
  evaluation: ATSEvaluationResult,
  resume: StructuredResume,
  jobDescription: AnalyzedJD,
): Promise<PotentialScoreResult> {
  const raw = await jsonPost<unknown>("/api/ats/potential", {
    evaluation,
    resume,
    jobDescription,
  });
  return PotentialScoreResultSchema.parse(raw);
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

export async function fetchRecommendations(
  evaluation: ATSEvaluationResult,
  resume: StructuredResume,
  jobDescription: AnalyzedJD,
): Promise<RecommendationReport> {
  const raw = await jsonPost<unknown>("/api/ats/recommendations", {
    evaluation,
    resume,
    jobDescription,
  });
  return RecommendationReportSchema.parse(raw);
}
