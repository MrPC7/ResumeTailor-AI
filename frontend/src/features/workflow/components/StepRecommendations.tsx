"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ATSComparisonCard } from "@/components/ats/ATSComparisonCard";
import { RecommendationPanel } from "@/components/recommendations/RecommendationPanel";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { compareATS } from "@/features/workflow/services/ats.service";
import { customizeResume } from "@/features/workflow/services/customize-resume.service";
import type { OptimizeResult } from "@/features/workflow/types/workflow.types";

type Phase = "select" | "applying" | "done";

export function StepRecommendations() {
  const uploadData = useWorkflowStore((s) => s.uploadData);
  const jdData = useWorkflowStore((s) => s.jdData);
  const atsStepData = useWorkflowStore((s) => s.atsStepData);
  const storedOptimizeResult = useWorkflowStore((s) => s.optimizeResult);
  const updateSelectedRecommendations = useWorkflowStore((s) => s.updateSelectedRecommendations);
  const completeRecommendations = useWorkflowStore((s) => s.completeRecommendations);
  const goPrev = useWorkflowStore((s) => s.goPrev);

  // If we already have an optimizeResult cached, start in "done" mode.
  const [phase, setPhase] = useState<Phase>(storedOptimizeResult ? "done" : "select");
  const [optimizeResult, setOptimizeResult] = useState<OptimizeResult | null>(storedOptimizeResult);
  const [appliedSummary, setAppliedSummary] = useState<{
    accepted: string[];
    rejected: string[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedActions = atsStepData?.selectedRecommendations ?? {};

  const handleSelectionChange = (next: Record<string, boolean>) => {
    updateSelectedRecommendations(next);
    // If they change selection after seeing done state, go back to select.
    if (phase === "done") {
      setPhase("select");
      setOptimizeResult(null);
    }
  };

  const applyMutation = useMutation({
    mutationFn: async () => {
      const atsResult = atsStepData!.atsResult;
      const recReport = atsStepData!.recReport;
      const resume = uploadData!.resume;
      const analyzedJD = jdData!.analyzedJD;

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
        for (const action of atsResult.recommendedActions) {
          if (selectedActions[action]) {
            acceptedRecs.push(action);
          } else {
            rejectedRecs.push(action);
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
      const outcome: OptimizeResult = {
        customizedResume: result.customizedResume,
        atsComparison: result.atsComparison,
      };
      setOptimizeResult(outcome);
      setAppliedSummary({ accepted: result.acceptedRecs, rejected: result.rejectedRecs });
      setPhase("done");
    },
    onError: (e) => {
      setError(e instanceof Error ? e.message : "Failed to optimize resume.");
    },
  });

  const acceptedCount = Object.values(selectedActions).filter(Boolean).length;

  const handleApply = () => {
    if (acceptedCount === 0) return;
    setError(null);
    setPhase("applying");
    applyMutation.mutate();
  };

  const handleContinue = () => {
    if (optimizeResult) completeRecommendations(optimizeResult);
  };

  // ── Applying ──────────────────────────────────────────────────────────
  if (phase === "applying") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Applying Recommendations</CardTitle>
          <CardDescription>Customizing your resume with AI...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center py-8">
            <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
            <p className="mt-3 text-sm text-slate-500">
              Applying {acceptedCount} recommendation{acceptedCount !== 1 ? "s" : ""}...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // ── Done ──────────────────────────────────────────────────────────────
  if (phase === "done" && optimizeResult) {
    const { atsComparison } = optimizeResult;
    const delta = atsComparison.afterScore - atsComparison.beforeScore;

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-emerald-600" />
              Optimization Complete
            </CardTitle>
            <CardDescription>
              {delta > 0
                ? `ATS score improved by ${delta} points.`
                : "Resume customized. Review the comparison below."}
            </CardDescription>
          </CardHeader>
        </Card>

        <ATSComparisonCard comparison={atsComparison} />

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
          <Button variant="outline" size="sm" onClick={() => setPhase("select")}>
            ← Adjust Selections
          </Button>
          <Button onClick={handleContinue} className="gap-2">
            Preview Resume →
          </Button>
        </div>
      </div>
    );
  }

  // ── Select mode ───────────────────────────────────────────────────────
  const recReport = atsStepData?.recReport ?? null;
  const atsResult = atsStepData?.atsResult;
  const potentialScore = atsStepData?.potentialScore;

  return (
    <div className="space-y-6">
      {recReport ? (
        <RecommendationPanel
          report={recReport}
          currentScore={atsResult?.overallScore ?? 0}
          potentialScore={potentialScore?.potentialScore ?? (atsResult?.overallScore ?? 0)}
          selectedIds={selectedActions}
          onSelectionChange={handleSelectionChange}
        />
      ) : (
        /* Fallback: flat recommended-actions list when structured report isn't available */
        <Card>
          <CardHeader>
            <CardTitle>Recommended Actions</CardTitle>
            <CardDescription>
              Select the improvements to apply to your resume.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {atsResult && atsResult.recommendedActions.length > 0 ? (
              <ul className="space-y-2">
                {atsResult.recommendedActions.map((action, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      id={`action-${i}`}
                      className="mt-1"
                      checked={selectedActions[action] ?? true}
                      onChange={(e) =>
                        handleSelectionChange({ ...selectedActions, [action]: e.target.checked })
                      }
                    />
                    <label htmlFor={`action-${i}`} className="text-sm text-slate-700">
                      {action}
                    </label>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No recommendations available.</p>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <Button variant="outline" size="sm" onClick={goPrev}>
          ← Previous
        </Button>
        <Button onClick={handleApply} disabled={acceptedCount === 0}>
          {acceptedCount > 0
            ? `Apply ${acceptedCount} Recommendation${acceptedCount !== 1 ? "s" : ""} →`
            : "Select at least one recommendation"}
        </Button>
      </div>
    </div>
  );
}
