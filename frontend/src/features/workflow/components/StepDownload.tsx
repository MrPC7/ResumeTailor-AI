"use client";

import { useState } from "react";
import { RotateCcw } from "lucide-react";
import { RecruiterDashboard } from "@/components/recruiter";
import { CoverLetterTab } from "@/components/cover-letter/CoverLetterTab";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { cn } from "@/lib/utils";

type TabId = "summary" | "cover-letter";

export function StepDownload() {
  const recruiterData = useWorkflowStore((s) => s.recruiterData!);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const reset = useWorkflowStore((s) => s.reset);

  const [activeTab, setActiveTab] = useState<TabId>("summary");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-center">
        <p className="text-sm font-medium text-emerald-700">
          ✓ Evaluation complete — review your results below
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 rounded-lg border bg-white p-1" role="tablist">
        {(
          [
            { id: "summary", label: "Evaluation Summary" },
            { id: "cover-letter", label: "Cover Letter" },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
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

      {/* Tab content */}
      {activeTab === "summary" && <RecruiterDashboard evaluation={recruiterData.evaluation} />}
      {activeTab === "cover-letter" && <CoverLetterTab />}

      {/* Actions */}
      <div className="flex justify-between">
        <button
          onClick={goPrev}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          ← Back
        </button>
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          <RotateCcw className="h-4 w-4" />
          Start New Evaluation
        </button>
      </div>
    </div>
  );
}
