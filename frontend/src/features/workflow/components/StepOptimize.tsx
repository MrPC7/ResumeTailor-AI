"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  TrendingUp,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ATSScoreCard } from "@/components/ats/ATSScoreCard";
import { ATSBreakdown } from "@/components/ats/ATSBreakdown";
import { ATSComparisonCard } from "@/components/ats/ATSComparisonCard";
import { MatchedKeywords } from "@/components/ats/MatchedKeywords";
import { MissingKeywords } from "@/components/ats/MissingKeywords";
import { RecommendationPanel } from "@/components/recommendations/RecommendationPanel";
import { analyzeATS, compareATS, predictPotentialScore, fetchRecommendations } from "@/features/workflow/services/ats.service";
import { customizeResume } from "@/features/workflow/services/customize-resume.service";
import type {
  AnalyzedJD,
  ATSEvaluationResult,
  OptimizeResult,
  PotentialScoreResult,
  RecommendationReport,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";

type Phase = "loading" | "review" | "applying" | "done" | "error";

type Props = {
  resume: StructuredResume;
  analyzedJD: AnalyzedJD;
  onComplete: (result: OptimizeResult) => void;
  onReset: () => void;
};

export function StepOptimize({ resume, analyzedJD, onComplete, onReset }: Props) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [atsResult, setAtsResult] = useState<ATSEvaluationResult | null>(null);
  const [potentialScore, setPotentialScore] = useState<PotentialScoreResult | null>(null);
  const [recReport, setRecReport] = useState<RecommendationReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedActions, setSelectedActions] = useState<Record<string, boolean>>({});
  const [optimizeResult, setOptimizeResult] = useState<OptimizeResult | null>(null);
  const [appliedSummary, setAppliedSummary] = useState<{ accepted: string[]; rejected: string[] } | null>(null);
  const startedRef = useRef(false);

  // ── Phase 1: Auto-compute original ATS score ─────────────────────────
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    async function run() {
      try {
        const result = await analyzeATS(resume, analyzedJD);
        setAtsResult(result);
        // Fetch potential score (non-blocking — don't fail the whole flow)
        predictPotentialScore(result, resume, analyzedJD)
          .then(setPotentialScore)
          .catch(() => {}); // silently ignore
        // Fetch structured recommendations (non-blocking)
        fetchRecommendations(result, resume, analyzedJD)
          .then((report) => {
            setRecReport(report);
            // Default: all recs accepted
            const defaults: Record<string, boolean> = {};
            for (const group of report.groups) {
              for (const rec of group.recommendations) {
                defaults[rec.id] = true;
              }
            }
            setSelectedActions(defaults);
          })
          .catch(() => {}); // silently ignore
        setPhase("review");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to analyze resume.");
        setPhase("error");
      }
    }

    void run();
  }, [resume, analyzedJD]);

  // ── Apply accepted recommendations ───────────────────────────────────
  const applyMutation = useMutation({
    mutationFn: async () => {
      // Build accepted and rejected recommendation lists
      const acceptedRecs: string[] = [];
      const rejectedRecs: string[] = [];

      if (recReport) {
        for (const group of recReport.groups) {
          for (const rec of group.recommendations) {
            if (selectedActions[rec.id]) {
              acceptedRecs.push(rec.title);
            } else {
              rejectedRecs.push(rec.title);
            }
          }
        }
      } else {
        // Fallback to flat recommendedActions if recs never loaded
        for (let i = 0; i < atsResult!.recommendedActions.length; i++) {
          if (selectedActions[String(i)]) {
            acceptedRecs.push(atsResult!.recommendedActions[i]);
          } else {
            rejectedRecs.push(atsResult!.recommendedActions[i]);
          }
        }
      }

      const { customizedResume } = await customizeResume(
        resume,
        analyzedJD,
        acceptedRecs,
        rejectedRecs,
      );
      const atsComparison = await compareATS(resume, customizedResume, analyzedJD);

      return { customizedResume, atsComparison, acceptedRecs, rejectedRecs };
    },
    onSuccess: (result) => {
      setOptimizeResult({ customizedResume: result.customizedResume, atsComparison: result.atsComparison });
      setAppliedSummary({ accepted: result.acceptedRecs, rejected: result.rejectedRecs });
      setPhase("done");
    },
    onError: (e) => {
      setError(e instanceof Error ? e.message : "Failed to optimize resume.");
      setPhase("error");
    },
  });

  const handleApply = () => {
    if (acceptedCount === 0) return;
    setPhase("applying");
    applyMutation.mutate();
  };

  const acceptedCount = Object.values(selectedActions).filter(Boolean).length;

  // ── Loading state ────────────────────────────────────────────────────
  if (phase === "loading") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analyzing Your Resume</CardTitle>
          <CardDescription>AI is evaluating your resume against the job description...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center py-8">
            <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
            <p className="mt-3 text-sm text-slate-500">Running AI-powered ATS evaluation...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────
  if (phase === "error") {
    return (
      <Card>
        <CardContent className="space-y-4 pt-6">
          <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
          <Button className="w-full" variant="outline" onClick={onReset}>
            ← Start Over
          </Button>
        </CardContent>
      </Card>
    );
  }

  // ── Done state ───────────────────────────────────────────────────────
  if (phase === "done" && optimizeResult) {
    const { atsComparison } = optimizeResult;
    const delta = atsComparison.afterScore - atsComparison.beforeScore;

    return (
      <div className="space-y-6">
        {/* Header */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-emerald-600" />
              Optimization Complete
            </CardTitle>
            <CardDescription>
              Your resume has been optimized.{" "}
              {delta > 0
                ? `ATS score improved by ${delta} points.`
                : "Review the detailed breakdown below."}
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Actual ATS Improvement — before/after with per-dimension */}
        <ATSComparisonCard comparison={atsComparison} />

        {/* After-optimization score breakdown */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Optimized Score Breakdown</CardTitle>
            <CardDescription>Per-dimension scores after optimization.</CardDescription>
          </CardHeader>
          <CardContent>
            <ATSBreakdown scores={atsComparison.after.scores} />
          </CardContent>
        </Card>

        {/* Strengths & Weaknesses — post-optimization */}
        <div className="grid gap-4 sm:grid-cols-2">
          {atsComparison.after.strengths.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ThumbsUp className="h-4 w-4 text-emerald-600" />
                  Strengths ({atsComparison.after.strengths.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1.5">
                  {atsComparison.after.strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                      {s}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {atsComparison.after.weaknesses.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ThumbsDown className="h-4 w-4 text-amber-600" />
                  Remaining Gaps ({atsComparison.after.weaknesses.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1.5">
                  {atsComparison.after.weaknesses.map((w, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                      {w}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Matched + Missing Keywords — post-optimization */}
        <div className="grid gap-4 sm:grid-cols-2">
          {atsComparison.after.matchedKeywords.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">
                  Matched Keywords ({atsComparison.after.matchedKeywords.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <MatchedKeywords keywords={atsComparison.after.matchedKeywords} />
              </CardContent>
            </Card>
          )}

          {atsComparison.after.missingKeywords.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">
                  Still Missing ({atsComparison.after.missingKeywords.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <MissingKeywords keywords={atsComparison.after.missingKeywords} />
              </CardContent>
            </Card>
          )}
        </div>

        {/* Resume Optimization Summary */}
        {appliedSummary && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Optimization Summary</CardTitle>
              <CardDescription>
                {appliedSummary.accepted.length} applied, {appliedSummary.rejected.length} skipped
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {appliedSummary.accepted.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-emerald-600">
                    Applied
                  </p>
                  <ul className="space-y-1">
                    {appliedSummary.accepted.map((a, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                        <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
                        {a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {appliedSummary.rejected.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Skipped
                    </p>
                    <ul className="space-y-1">
                      {appliedSummary.rejected.map((r, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                          <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}

        <div className="flex items-center justify-between gap-3">
          <Button variant="ghost" size="sm" onClick={onReset}>
            ← Start Over
          </Button>
          <Button onClick={() => onComplete(optimizeResult)}>
            Proceed to Download →
          </Button>
        </div>
      </div>
    );
  }

  // ── Review state ─────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Original ATS Score + Confidence */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Your Current ATS Score</CardTitle>
              <CardDescription>
                AI-powered evaluation against this job description.
              </CardDescription>
            </div>
            <div className="flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-slate-500" />
              <span className="text-xs font-medium text-slate-600">
                {atsResult!.confidence}% confidence
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col items-center py-4">
          <ATSScoreCard score={atsResult!.overallScore} size={140} label="Overall ATS Score" />
        </CardContent>
      </Card>

      {/* Potential Score Prediction */}
      {potentialScore && potentialScore.improvementPotential > 0 && (
        <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardContent className="flex items-center justify-between py-4 px-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800">
                  Potential Score: {potentialScore.potentialScore}
                </p>
                <p className="text-xs text-slate-500">
                  Up to +{potentialScore.improvementPotential} points achievable by applying recommendations
                </p>
              </div>
            </div>
            <div className="flex flex-col items-end">
              <span className="text-2xl font-extrabold tabular-nums text-blue-700">
                {potentialScore.currentScore} → {potentialScore.potentialScore}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Score Breakdown */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Score Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <ATSBreakdown scores={atsResult!.scores} />
        </CardContent>
      </Card>

      {/* Strengths & Weaknesses */}
      <div className="grid gap-4 sm:grid-cols-2">
        {atsResult!.strengths.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <ThumbsUp className="h-4 w-4 text-emerald-600" />
                Strengths ({atsResult!.strengths.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1.5">
                {atsResult!.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                    {s}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {atsResult!.weaknesses.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <ThumbsDown className="h-4 w-4 text-amber-600" />
                Weaknesses ({atsResult!.weaknesses.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1.5">
                {atsResult!.weaknesses.map((w, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    {w}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Matched & Missing Keywords */}
      <div className="grid gap-4 sm:grid-cols-2">
        {atsResult!.matchedKeywords.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Matched Keywords ({atsResult!.matchedKeywords.length})
              </CardTitle>
              <CardDescription>Keywords from the JD found in your resume.</CardDescription>
            </CardHeader>
            <CardContent>
              <MatchedKeywords keywords={atsResult!.matchedKeywords} />
            </CardContent>
          </Card>
        )}

        {atsResult!.missingKeywords.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Missing Keywords ({atsResult!.missingKeywords.length})
              </CardTitle>
              <CardDescription>These keywords were not found in your resume.</CardDescription>
            </CardHeader>
            <CardContent>
              <MissingKeywords keywords={atsResult!.missingKeywords} />
            </CardContent>
          </Card>
        )}
      </div>

      <Separator />

      {/* AI Recommendations — grouped panel with live score updates */}
      {recReport && recReport.groups.length > 0 ? (
        <RecommendationPanel
          report={recReport}
          currentScore={atsResult!.overallScore}
          potentialScore={potentialScore?.potentialScore ?? atsResult!.overallScore}
          selectedIds={selectedActions}
          onSelectionChange={setSelectedActions}
        />
      ) : !recReport ? (
        <Card>
          <CardContent className="flex flex-col items-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            <p className="mt-2 text-sm text-slate-500">Loading recommendations...</p>
          </CardContent>
        </Card>
      ) : null}

      {/* Apply button */}
      <div className="flex items-center justify-between gap-3">
        <Button variant="ghost" size="sm" onClick={onReset}>
          ← Start Over
        </Button>
        <Button
          onClick={handleApply}
          disabled={acceptedCount === 0 || phase === "applying"}
          className="gap-2"
        >
          {phase === "applying" ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Applying Changes...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Apply {acceptedCount} Action{acceptedCount !== 1 ? "s" : ""}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
