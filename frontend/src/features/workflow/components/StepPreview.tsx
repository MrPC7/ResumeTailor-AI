"use client";

import { useEffect, useRef, useState } from "react";
import { RecruiterDashboard } from "@/components/recruiter";
import { ResumeView } from "@/components/resume/ResumeView";
import { ResumeDiff } from "@/components/resume/ResumeDiff";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { customizeResume } from "@/features/workflow/services/customize-resume.service";
import { cn } from "@/lib/utils";

type TabId = "optimized" | "diff" | "recruiter";
type Phase = "loading" | "ready" | "error";

export function StepPreview() {
  const uploadData = useWorkflowStore((s) => s.uploadData!);
  const jdData = useWorkflowStore((s) => s.jdData!);
  const recruiterData = useWorkflowStore((s) => s.recruiterData!);
  const suggestionsData = useWorkflowStore((s) => s.suggestionsData!);
  const previewData = useWorkflowStore((s) => s.previewData);
  const setPreviewData = useWorkflowStore((s) => s.setPreviewData);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const navigateTo = useWorkflowStore((s) => s.navigateTo);

  const [activeTab, setActiveTab] = useState<TabId>("optimized");
  const [phase, setPhase] = useState<Phase>(previewData ? "ready" : "loading");
  const startedRef = useRef(false);

  useEffect(() => {
    if (previewData || startedRef.current) return;
    startedRef.current = true;

    async function run() {
      try {
        const selectedIds = Object.entries(suggestionsData.selectedSuggestions)
          .filter(([, v]) => v)
          .map(([id]) => id);
        const rejectedIds = Object.entries(suggestionsData.selectedSuggestions)
          .filter(([, v]) => !v)
          .map(([id]) => id);

        const result = await customizeResume(
          uploadData.resume,
          jdData.analyzedJD,
          selectedIds,
          rejectedIds
        );

        setPreviewData({ customizedResume: result.customizedResume });
        setPhase("ready");
      } catch {
        setPhase("error");
      }
    }

    void run();
  }, [previewData, uploadData, jdData, suggestionsData, setPreviewData]);

  if (phase === "loading") {
    return (
      <div className="flex flex-col items-center justify-center py-16" aria-busy="true">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-indigo-600" />
        <p className="mt-4 text-sm text-slate-500">Optimizing your resume...</p>
        <p className="mt-1 text-xs text-slate-400">Applying selected suggestions</p>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm font-medium text-red-700">
          Failed to optimize resume. Please try again.
        </p>
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

  const customizedResume = previewData!.customizedResume;

  const tabs: { id: TabId; label: string }[] = [
    { id: "optimized", label: "Optimized Resume" },
    { id: "diff", label: "Resume Diff" },
    { id: "recruiter", label: "Recruiter Review" },
  ];

  return (
    <div className="space-y-6">
      {/* Tab bar */}
      <div className="flex gap-1 rounded-lg border bg-white p-1" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            id={`tab-${tab.id}`}
            aria-controls={`tabpanel-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div role="tabpanel" id={`tabpanel-${activeTab}`} aria-labelledby={`tab-${activeTab}`}>
        {activeTab === "optimized" && <ResumeView resume={customizedResume} />}
        {activeTab === "diff" && (
          <ResumeDiff original={uploadData.resume} customized={customizedResume} />
        )}
        {activeTab === "recruiter" && <RecruiterDashboard evaluation={recruiterData.evaluation} />}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={goPrev}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          ← Back
        </button>
        <button
          onClick={() => navigateTo("download")}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Continue to Download →
        </button>
      </div>
    </div>
  );
}
