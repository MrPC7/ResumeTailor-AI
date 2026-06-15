"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ATSScoreCard } from "@/components/ats/ATSScoreCard";
import { ATSBreakdown } from "@/components/ats/ATSBreakdown";
import { MatchedKeywords } from "@/components/ats/MatchedKeywords";
import { MissingKeywords } from "@/components/ats/MissingKeywords";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import {
  analyzeATS,
  fetchRecommendations,
  predictPotentialScore,
} from "@/features/workflow/services/ats.service";
import type { ATSStepData } from "@/features/workflow/types/workflow.types";
import { Loader2 } from "lucide-react";

type Phase = "loading" | "ready" | "error";

export function StepATS() {
  const uploadData = useWorkflowStore((s) => s.uploadData);
  const jdData = useWorkflowStore((s) => s.jdData);
  const storedAtsStepData = useWorkflowStore((s) => s.atsStepData);
  const completeATS = useWorkflowStore((s) => s.completeATS);
  const goPrev = useWorkflowStore((s) => s.goPrev);

  const [phase, setPhase] = useState<Phase>(storedAtsStepData ? "ready" : "loading");
  const [atsStepData, setAtsStepData] = useState<ATSStepData | null>(storedAtsStepData);
  const [error, setError] = useState<string | null>(null);
  const startedRef = useRef(false);

  // Run ATS analysis only if we don't have cached data.
  useEffect(() => {
    if (storedAtsStepData || startedRef.current) return;
    if (!uploadData || !jdData) return;
    startedRef.current = true;

    async function run() {
      try {
        const atsResult = await analyzeATS(uploadData!.resume, jdData!.analyzedJD);

        // Build default "all selected" map
        const defaultSelections: Record<string, boolean> = {};
        for (const action of atsResult.recommendedActions) {
          defaultSelections[action] = true;
        }

        const initialData: ATSStepData = {
          atsResult,
          potentialScore: null,
          recReport: null,
          selectedRecommendations: defaultSelections,
        };

        setAtsStepData(initialData);
        setPhase("ready");

        // Fetch potential score and recommendations in parallel (non-blocking).
        const [potentialScore, recReport] = await Promise.allSettled([
          predictPotentialScore(atsResult, uploadData!.resume, jdData!.analyzedJD),
          fetchRecommendations(atsResult, uploadData!.resume, jdData!.analyzedJD),
        ]);

        setAtsStepData((prev) => {
          if (!prev) return prev;
          const ps =
            potentialScore.status === "fulfilled" ? potentialScore.value : null;
          const rr = recReport.status === "fulfilled" ? recReport.value : null;

          // Build recommendation-level default selections from the full report.
          const recSelections: Record<string, boolean> = { ...prev.selectedRecommendations };
          if (rr) {
            for (const group of rr.groups) {
              for (const rec of group.recommendations) {
                if (!(rec.id in recSelections)) {
                  recSelections[rec.id] = true;
                }
              }
            }
          }

          return { ...prev, potentialScore: ps, recReport: rr, selectedRecommendations: recSelections };
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to analyze resume.");
        setPhase("error");
      }
    }

    void run();
  }, [uploadData, jdData, storedAtsStepData]);

  const handleContinue = () => {
    if (!atsStepData) return;
    completeATS(atsStepData);
  };

  // ── Loading ───────────────────────────────────────────────────────────
  if (phase === "loading") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analyzing Your Resume</CardTitle>
          <CardDescription>
            AI is evaluating your resume against the job description...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center py-8">
            <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
            <p className="mt-3 text-sm text-slate-500">Running AI-powered ATS evaluation...</p>
          </div>
          <div className="mt-4 flex justify-start">
            <Button variant="outline" size="sm" onClick={goPrev}>
              ← Previous
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // ── Error ─────────────────────────────────────────────────────────────
  if (phase === "error") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>ATS Analysis Failed</CardTitle>
          <CardDescription>Something went wrong while evaluating your resume.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
          <div className="flex items-center justify-between gap-3">
            <Button variant="outline" size="sm" onClick={goPrev}>
              ← Previous
            </Button>
            <Button
              onClick={() => {
                startedRef.current = false;
                setError(null);
                setPhase("loading");
              }}
            >
              Retry Analysis
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { atsResult, potentialScore } = atsStepData!;

  // ── Ready ─────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Overall ATS Score */}
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
                {atsResult.confidence}% confidence
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col items-center py-4">
          <ATSScoreCard score={atsResult.overallScore} size={140} label="Overall ATS Score" />
        </CardContent>
      </Card>

      {/* Potential score banner */}
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
                  Up to +{potentialScore.improvementPotential} points achievable with recommendations
                </p>
              </div>
            </div>
            <span className="text-2xl font-extrabold tabular-nums text-blue-700">
              {potentialScore.potentialScore}
            </span>
          </CardContent>
        </Card>
      )}

      {/* Score breakdown */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Score Breakdown</CardTitle>
          <CardDescription>Per-dimension match scores.</CardDescription>
        </CardHeader>
        <CardContent>
          <ATSBreakdown scores={atsResult.scores} />
        </CardContent>
      </Card>

      {/* Strengths & Weaknesses */}
      <div className="grid gap-4 sm:grid-cols-2">
        {atsResult.strengths.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <ThumbsUp className="h-4 w-4 text-emerald-600" />
                Strengths ({atsResult.strengths.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1.5">
                {atsResult.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                    {s}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {atsResult.weaknesses.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <ThumbsDown className="h-4 w-4 text-amber-600" />
                Gaps ({atsResult.weaknesses.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1.5">
                {atsResult.weaknesses.map((w, i) => (
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

      {/* Keywords */}
      <div className="grid gap-4 sm:grid-cols-2">
        {atsResult.matchedKeywords.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Matched Keywords ({atsResult.matchedKeywords.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <MatchedKeywords keywords={atsResult.matchedKeywords} />
            </CardContent>
          </Card>
        )}
        {atsResult.missingKeywords.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Missing Keywords ({atsResult.missingKeywords.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <MissingKeywords keywords={atsResult.missingKeywords} />
            </CardContent>
          </Card>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between gap-3">
        <Button variant="outline" size="sm" onClick={goPrev}>
          ← Previous
        </Button>
        <Button onClick={handleContinue}>
          View Recommendations →
        </Button>
      </div>
    </div>
  );
}
