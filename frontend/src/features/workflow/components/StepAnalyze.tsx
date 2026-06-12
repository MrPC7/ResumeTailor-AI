"use client";

import { useMutation } from "@tanstack/react-query";
import { AlertCircle, Check, Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchResumeDiff } from "@/features/resume-diff/services/resume-diff.service";
import { customizeResume } from "@/features/workflow/services/customize-resume.service";
import { fetchGapAnalysis } from "@/features/workflow/services/gap-analysis.service";
import { fetchMatchScore } from "@/features/workflow/services/match-score.service";
import type {
  AnalysisResult,
  AnalyzedJD,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";
import { cn } from "@/lib/utils";

type Phase = "idle" | "scoring" | "gaps" | "customizing" | "diff" | "done" | "error";

const PHASES: { id: Phase; label: string }[] = [
  { id: "scoring", label: "Calculating ATS match score" },
  { id: "gaps", label: "Identifying skill gaps" },
  { id: "customizing", label: "Customizing resume for this role" },
  { id: "diff", label: "Computing changes" },
];

const PHASE_ORDER: Phase[] = ["idle", "scoring", "gaps", "customizing", "diff", "done", "error"];

type Props = {
  resume: StructuredResume;
  analyzedJD: AnalyzedJD;
  onComplete: (result: AnalysisResult) => void;
};

export function StepAnalyze({ resume, analyzedJD, onComplete }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const startedRef = useRef(false);

  const mutation = useMutation({
    mutationFn: async (): Promise<AnalysisResult> => {
      setPhase("scoring");
      const [matchScore, gapAnalysis] = await Promise.all([
        fetchMatchScore(resume, analyzedJD),
        fetchGapAnalysis(resume, analyzedJD),
      ]);

      setPhase("customizing");
      const { customizedResume, suggestions } = await customizeResume(
        resume,
        analyzedJD,
        gapAnalysis
      );

      setPhase("diff");
      const { diff } = await fetchResumeDiff(resume, customizedResume);

      setPhase("done");
      return { matchScore, gapAnalysis, customizedResume, suggestions, diff };
    },
    onSuccess: (result) => {
      // Brief pause so the user sees all checkmarks before advancing
      setTimeout(() => onComplete(result), 800);
    },
    onError: () => {
      setPhase("error");
    },
  });

  useEffect(() => {
    if (!startedRef.current) {
      startedRef.current = true;
      setTimeout(() => mutation.mutate(), 400);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const currentPhaseIndex = PHASE_ORDER.indexOf(phase);

  const getPhaseStatus = (phaseId: Phase): "pending" | "active" | "done" => {
    const phaseIdx = PHASE_ORDER.indexOf(phaseId);
    if (phase === "done" || currentPhaseIndex > phaseIdx) return "done";
    if (currentPhaseIndex === phaseIdx) return "active";
    return "pending";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Analyzing Your Resume</CardTitle>
        <CardDescription>
          Running AI-powered analysis against the job description. This may take a moment.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <ul className="space-y-3">
          {PHASES.map((p) => {
            const status = getPhaseStatus(p.id);
            return (
              <li key={p.id} className="flex items-center gap-3">
                <div
                  className={cn(
                    "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 transition-colors",
                    status === "done" && "border-emerald-500 bg-emerald-500 text-white",
                    status === "active" && "border-slate-900 bg-white",
                    status === "pending" && "border-slate-200 bg-white"
                  )}
                >
                  {status === "done" && <Check className="h-3.5 w-3.5" />}
                  {status === "active" && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-700" />
                  )}
                  {status === "pending" && <span className="h-2 w-2 rounded-full bg-slate-200" />}
                </div>
                <span
                  className={cn(
                    "text-sm transition-colors",
                    status === "done" && "text-emerald-700 line-through decoration-emerald-400",
                    status === "active" && "font-medium text-slate-900",
                    status === "pending" && "text-slate-400"
                  )}
                >
                  {p.label}
                </span>
              </li>
            );
          })}
        </ul>

        {/* Error state */}
        {phase === "error" && (
          <div className="space-y-3">
            <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
              <p className="text-sm text-red-700">
                {mutation.error?.message ?? "Analysis failed."}
              </p>
            </div>
            <Button
              className="w-full"
              variant="outline"
              onClick={() => {
                setPhase("idle");
                startedRef.current = false;
                setTimeout(() => {
                  startedRef.current = true;
                  mutation.mutate();
                }, 100);
              }}
            >
              Retry Analysis
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
