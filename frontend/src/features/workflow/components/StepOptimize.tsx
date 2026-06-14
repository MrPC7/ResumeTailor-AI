"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  AlertCircle,
  Check,
  ChevronDown,
  ChevronRight,
  Loader2,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  TrendingUp,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ATSScoreCard } from "@/components/ats/ATSScoreCard";
import { ATSBreakdown } from "@/components/ats/ATSBreakdown";
import { ATSComparisonCard } from "@/components/ats/ATSComparisonCard";
import { MissingKeywords } from "@/components/ats/MissingKeywords";
import { analyzeATS, compareATS, predictPotentialScore, fetchRecommendations } from "@/features/workflow/services/ats.service";
import { customizeResume } from "@/features/workflow/services/customize-resume.service";
import type {
  AnalyzedJD,
  ATSEvaluationResult,
  ImpactLevel,
  OptimizeResult,
  PotentialScoreResult,
  RecommendationReport,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";
import { cn } from "@/lib/utils";

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
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});
  const [optimizeResult, setOptimizeResult] = useState<OptimizeResult | null>(null);
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
    mutationFn: async (): Promise<OptimizeResult> => {
      // Build accepted recommendations list from grouped rec report
      const acceptedRecs: string[] = [];
      if (recReport) {
        for (const group of recReport.groups) {
          for (const rec of group.recommendations) {
            if (selectedActions[rec.id]) {
              acceptedRecs.push(rec.title);
            }
          }
        }
      } else {
        // Fallback to flat recommendedActions if recs never loaded
        acceptedRecs.push(
          ...atsResult!.recommendedActions.filter((_, i) => selectedActions[String(i)]),
        );
      }

      const gapAnalysis = {
        matchedSkills: [] as string[],
        missingSkills: atsResult!.missingKeywords,
        recommendations: acceptedRecs,
      };

      const { customizedResume } = await customizeResume(resume, analyzedJD, gapAnalysis);
      const atsComparison = await compareATS(resume, customizedResume, analyzedJD);

      return { customizedResume, atsComparison };
    },
    onSuccess: (result) => {
      setOptimizeResult(result);
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

  const toggleAction = (id: string) => {
    setSelectedActions((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleGroup = (groupId: string) => {
    setCollapsedGroups((prev) => ({ ...prev, [groupId]: !prev[groupId] }));
  };

  const acceptedCount = Object.values(selectedActions).filter(Boolean).length;

  const impactBadge = (level: ImpactLevel) => {
    const styles: Record<ImpactLevel, string> = {
      critical: "bg-red-100 text-red-700",
      high: "bg-orange-100 text-orange-700",
      medium: "bg-yellow-100 text-yellow-700",
      low: "bg-slate-100 text-slate-600",
    };
    return (
      <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase", styles[level])}>
        {level}
      </span>
    );
  };

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
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-emerald-600" />
              Optimization Complete
            </CardTitle>
            <CardDescription>
              Your resume has been optimized based on your selected recommendations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ATSComparisonCard comparison={optimizeResult.atsComparison} />
          </CardContent>
        </Card>

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

      {/* Missing Keywords */}
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

      <Separator />

      {/* AI Recommendations — grouped by category */}
      {recReport && recReport.groups.length > 0 ? (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Zap className="h-4 w-4 text-amber-500" />
                  Recommendations
                </CardTitle>
                <CardDescription>
                  Estimated total ATS gain: +{recReport.totalEstimatedGain} points. Accept or reject each item.
                </CardDescription>
              </div>
              <span className="text-xs font-medium text-slate-500">
                {acceptedCount} selected
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {recReport.groups.map((group) => {
              const isCollapsed = collapsedGroups[group.groupId] ?? false;
              const groupSelectedCount = group.recommendations.filter(
                (r) => selectedActions[r.id],
              ).length;
              const groupPoints = group.recommendations.reduce(
                (sum, r) => sum + r.estimatedPoints,
                0,
              );

              return (
                <div key={group.groupId} className="rounded-lg border border-slate-200">
                  {/* Group header — click to collapse */}
                  <button
                    type="button"
                    className="flex w-full items-center justify-between px-4 py-2.5 text-left hover:bg-slate-50 transition-colors"
                    onClick={() => toggleGroup(group.groupId)}
                  >
                    <div className="flex items-center gap-2">
                      {isCollapsed ? (
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-slate-400" />
                      )}
                      <span className="text-sm font-semibold text-slate-800">
                        {group.groupTitle}
                      </span>
                      <span className="text-xs text-slate-400">
                        ({groupSelectedCount}/{group.recommendations.length})
                      </span>
                    </div>
                    <span className="text-xs font-medium text-blue-600">
                      +{groupPoints} pts
                    </span>
                  </button>

                  {/* Recommendation items */}
                  {!isCollapsed && (
                    <div className="space-y-1 px-3 pb-3">
                      {group.recommendations.map((rec) => {
                        const isChecked = selectedActions[rec.id] ?? false;
                        return (
                          <div
                            key={rec.id}
                            className={cn(
                              "flex items-start gap-2.5 rounded-md border px-3 py-2 cursor-pointer transition-colors",
                              isChecked
                                ? "border-emerald-200 bg-emerald-50"
                                : "border-slate-200 bg-slate-50 opacity-60",
                            )}
                            onClick={() => toggleAction(rec.id)}
                          >
                            <button
                              type="button"
                              className={cn(
                                "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border-2 transition-colors",
                                isChecked
                                  ? "border-emerald-600 bg-emerald-600 text-white"
                                  : "border-slate-300 bg-white",
                              )}
                              aria-label={isChecked ? `Reject: ${rec.title}` : `Accept: ${rec.title}`}
                            >
                              {isChecked && <Check className="h-2.5 w-2.5" />}
                            </button>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm font-medium text-slate-800">
                                  {rec.title}
                                </span>
                                {impactBadge(rec.impactLevel)}
                                <span className="text-[10px] text-blue-600 font-medium">
                                  +{rec.estimatedPoints} pts
                                </span>
                              </div>
                              <p className="mt-0.5 text-xs text-slate-500 leading-relaxed">
                                {rec.description}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      ) : !recReport ? (
        /* Fallback: show flat recommendedActions while recs are loading / if they failed */
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Recommended Actions</CardTitle>
            <CardDescription>
              AI-generated suggestions to improve your ATS score.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {atsResult!.recommendedActions.map((action, i) => {
              const isChecked = selectedActions[String(i)] ?? false;
              return (
                <div
                  key={i}
                  className={cn(
                    "flex items-center gap-2.5 rounded-md border px-3 py-2 cursor-pointer transition-colors",
                    isChecked
                      ? "border-emerald-200 bg-emerald-50"
                      : "border-slate-200 bg-slate-50 opacity-60",
                  )}
                  onClick={() => toggleAction(String(i))}
                >
                  <button
                    type="button"
                    className={cn(
                      "flex h-4 w-4 shrink-0 items-center justify-center rounded border-2 transition-colors",
                      isChecked
                        ? "border-emerald-600 bg-emerald-600 text-white"
                        : "border-slate-300 bg-white",
                    )}
                    aria-label={isChecked ? `Reject: ${action}` : `Accept: ${action}`}
                  >
                    {isChecked && <Check className="h-2.5 w-2.5" />}
                  </button>
                  <span className="text-sm text-slate-700">{action}</span>
                </div>
              );
            })}

            {atsResult!.recommendedActions.length === 0 && (
              <p className="text-sm text-slate-400 italic">
                No recommendations — your resume is already well-optimized!
              </p>
            )}
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
