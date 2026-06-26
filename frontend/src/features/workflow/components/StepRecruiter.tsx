"use client";

import { useEffect, useRef, useState } from "react";
import { RecruiterDashboard } from "@/components/recruiter";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { runEvaluation } from "@/features/workflow/services/evaluate.service";
import type { RecruiterStepData } from "@/features/workflow/types/workflow.types";

type Phase = "loading" | "ready" | "error";

export function StepRecruiter() {
  const uploadData = useWorkflowStore((s) => s.uploadData);
  const jdData = useWorkflowStore((s) => s.jdData);
  const recruiterData = useWorkflowStore((s) => s.recruiterData);
  const completeRecruiter = useWorkflowStore((s) => s.completeRecruiter);
  const goPrev = useWorkflowStore((s) => s.goPrev);

  const [phase, setPhase] = useState<Phase>(recruiterData ? "ready" : "loading");
  const startedRef = useRef(false);

  useEffect(() => {
    if (recruiterData || startedRef.current) return;
    if (!uploadData || !jdData) return;

    startedRef.current = true;

    async function run() {
      try {
        const result = await runEvaluation(uploadData!.rawText, jdData!.jobDescription);

        const stepData: RecruiterStepData = {
          candidateProfile: result.candidateProfile,
          jobProfile: result.jobProfile,
          evaluation: result.evaluation,
        };

        completeRecruiter(stepData);
        setPhase("ready");
      } catch {
        setPhase("error");
      }
    }

    void run();
  }, [uploadData, jdData, recruiterData, completeRecruiter]);

  if (phase === "loading") {
    return (
      <div className="flex flex-col items-center justify-center py-16" aria-busy="true">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-indigo-600" />
        <p className="mt-4 text-sm text-slate-500">
          Analyzing your resume against the job description...
        </p>
        <p className="mt-1 text-xs text-slate-400">This may take 15-30 seconds</p>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm font-medium text-red-700">Evaluation failed. Please try again.</p>
        <button
          onClick={() => {
            startedRef.current = false;
            setPhase("loading");
          }}
          className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          Retry
        </button>
        <button
          onClick={goPrev}
          className="ml-3 rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Go Back
        </button>
      </div>
    );
  }

  const evaluation = recruiterData?.evaluation;
  if (!evaluation) return null;

  return (
    <div className="space-y-6">
      <RecruiterDashboard evaluation={evaluation} />

      <div className="flex justify-between">
        <button
          onClick={goPrev}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          ← Back
        </button>
        <button
          onClick={() => useWorkflowStore.getState().navigateTo("preview")}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Continue to Preview →
        </button>
      </div>
    </div>
  );
}
