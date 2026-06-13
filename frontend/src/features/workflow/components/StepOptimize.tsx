"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  AlertCircle,
  Check,
  Loader2,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ATSScoreCard } from "@/components/ats/ATSScoreCard";
import { ATSBreakdown } from "@/components/ats/ATSBreakdown";
import { ATSComparisonCard } from "@/components/ats/ATSComparisonCard";
import { MissingKeywords } from "@/components/ats/MissingKeywords";
import { KeywordHeatmap } from "@/components/ats/KeywordHeatmap";
import { analyzeATS, compareATS } from "@/features/workflow/services/ats.service";
import { customizeResume } from "@/features/workflow/services/customize-resume.service";
import type {
  AnalyzedJD,
  ATSAnalysisResult,
  OptimizeResult,
  RecommendationGroup,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";
import { cn } from "@/lib/utils";

// Key for tracking individual item selections: "groupIndex-itemIndex"
type ItemKey = `${number}-${number}`;

type Phase = "loading" | "review" | "applying" | "done" | "error";

type Props = {
  resume: StructuredResume;
  analyzedJD: AnalyzedJD;
  onComplete: (result: OptimizeResult) => void;
  onReset: () => void;
};

export function StepOptimize({ resume, analyzedJD, onComplete, onReset }: Props) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [atsResult, setAtsResult] = useState<ATSAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedItems, setSelectedItems] = useState<Record<ItemKey, boolean>>({});
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
        // Default: all items accepted
        const defaults: Record<ItemKey, boolean> = {};
        result.recommendations.forEach((group, gi) => {
          group.items.forEach((_, ii) => {
            defaults[`${gi}-${ii}`] = true;
          });
        });
        setSelectedItems(defaults);
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
      // Build accepted recommendations as flat strings for the customizer
      const acceptedRecs: string[] = [];
      atsResult!.recommendations.forEach((group, gi) => {
        const acceptedInGroup = group.items.filter(
          (_, ii) => selectedItems[`${gi}-${ii}`]
        );
        if (acceptedInGroup.length > 0) {
          acceptedRecs.push(`${group.title}: ${acceptedInGroup.join(", ")}`);
        }
      });

      const gapAnalysis = {
        matchedSkills: atsResult!.matchedKeywords,
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

  const toggleItem = (groupIndex: number, itemIndex: number) => {
    const key: ItemKey = `${groupIndex}-${itemIndex}`;
    setSelectedItems((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleGroup = (groupIndex: number, group: RecommendationGroup) => {
    const allSelected = group.items.every(
      (_, ii) => selectedItems[`${groupIndex}-${ii}`]
    );
    setSelectedItems((prev) => {
      const next = { ...prev };
      group.items.forEach((_, ii) => {
        next[`${groupIndex}-${ii}`] = !allSelected;
      });
      return next;
    });
  };

  const acceptedCount = Object.values(selectedItems).filter(Boolean).length;

  // ── Loading state ────────────────────────────────────────────────────
  if (phase === "loading") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analyzing Your Resume</CardTitle>
          <CardDescription>Computing ATS score against the job description...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center py-8">
            <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
            <p className="mt-3 text-sm text-slate-500">Running ATS analysis...</p>
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
      {/* Original ATS Score */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Your Current ATS Score</CardTitle>
          <CardDescription>
            How your original resume scores against this job description.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center py-4">
          <ATSScoreCard score={atsResult!.overallScore} size={140} label="Original Resume Score" />
        </CardContent>
      </Card>

      {/* Score Breakdown */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Score Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <ATSBreakdown scores={atsResult!.scores} />
        </CardContent>
      </Card>

      {/* Keywords */}
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

      {atsResult!.matchedKeywords.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              Matched Keywords ({atsResult!.matchedKeywords.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <KeywordHeatmap keywords={atsResult!.matchedKeywords} />
          </CardContent>
        </Card>
      )}

      <Separator />

      {/* Recommendations — per-item checkboxes */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Recommendations</CardTitle>
          <CardDescription>
            Review each suggestion. Accept or reject individual items.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {atsResult!.recommendations.map((group, gi) => {
            const groupSelected = group.items.filter(
              (_, ii) => selectedItems[`${gi}-${ii}`]
            ).length;
            const allSelected = groupSelected === group.items.length;

            return (
              <div key={gi} className="space-y-2">
                {/* Group title with select-all toggle */}
                <div
                  className="flex items-center gap-2 cursor-pointer"
                  onClick={() => toggleGroup(gi, group)}
                >
                  <button
                    type="button"
                    className={cn(
                      "flex h-4 w-4 shrink-0 items-center justify-center rounded border-2 transition-colors",
                      allSelected
                        ? "border-emerald-600 bg-emerald-600 text-white"
                        : groupSelected > 0
                          ? "border-emerald-400 bg-emerald-100"
                          : "border-slate-300 bg-white"
                    )}
                    aria-label={allSelected ? "Deselect all" : "Select all"}
                  >
                    {allSelected && <Check className="h-2.5 w-2.5" />}
                  </button>
                  <span className="text-sm font-semibold text-slate-800">{group.title}:</span>
                </div>

                {/* Individual items */}
                <div className="ml-6 space-y-1.5">
                  {group.items.map((item, ii) => {
                    const isChecked = selectedItems[`${gi}-${ii}`] ?? false;
                    return (
                      <div
                        key={ii}
                        className={cn(
                          "flex items-center gap-2.5 rounded-md border px-3 py-2 cursor-pointer transition-colors",
                          isChecked
                            ? "border-emerald-200 bg-emerald-50"
                            : "border-slate-200 bg-slate-50 opacity-60"
                        )}
                        onClick={() => toggleItem(gi, ii)}
                      >
                        <button
                          type="button"
                          className={cn(
                            "flex h-4 w-4 shrink-0 items-center justify-center rounded border-2 transition-colors",
                            isChecked
                              ? "border-emerald-600 bg-emerald-600 text-white"
                              : "border-slate-300 bg-white"
                          )}
                          aria-label={isChecked ? `Reject: ${item}` : `Accept: ${item}`}
                        >
                          {isChecked && <Check className="h-2.5 w-2.5" />}
                        </button>
                        <span className="text-sm text-slate-700">{item}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {atsResult!.recommendations.length === 0 && (
            <p className="text-sm text-slate-400 italic">
              No recommendations — your resume is already well-optimized!
            </p>
          )}
        </CardContent>
      </Card>

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
              Apply {acceptedCount} Change{acceptedCount !== 1 ? "s" : ""}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
