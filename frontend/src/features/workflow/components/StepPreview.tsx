"use client";

import { useState } from "react";
import { BeforeAfterComparison } from "@/components/recruiter/BeforeAfterComparison";
import { ResumeDiff } from "@/components/resume/ResumeDiff";
import { ResumeView } from "@/components/resume/ResumeView";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { cn } from "@/lib/utils";

type TabId = "optimized" | "diff" | "summary";

export function StepPreview() {
  const uploadData = useWorkflowStore((s) => s.uploadData!);
  const previewData = useWorkflowStore((s) => s.previewData);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const navigateTo = useWorkflowStore((s) => s.navigateTo);

  const [activeTab, setActiveTab] = useState<TabId>("optimized");

  if (!previewData) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-center">
        <p className="text-sm font-medium text-amber-800">
          Apply selected improvements before previewing the optimized resume.
        </p>
        <button
          onClick={goPrev}
          className="mt-4 rounded-md border border-amber-300 px-4 py-2 text-sm font-medium text-amber-800 hover:bg-amber-100 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
        >
          Back to Suggestions
        </button>
      </div>
    );
  }

  const tabs: { id: TabId; label: string }[] = [
    { id: "optimized", label: "Optimized Resume" },
    { id: "diff", label: "Resume Diff" },
    { id: "summary", label: "Improvement Summary" },
  ];

  return (
    <div className="space-y-6">
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

      <div role="tabpanel" id={`tabpanel-${activeTab}`} aria-labelledby={`tab-${activeTab}`}>
        {activeTab === "optimized" && <ResumeView resume={previewData.customizedResume} />}
        {activeTab === "diff" && (
          <ResumeDiff original={uploadData.resume} customized={previewData.customizedResume} />
        )}
        {activeTab === "summary" && <BeforeAfterComparison result={previewData.reevaluation} />}
      </div>

      <div className="flex justify-between">
        <button
          onClick={goPrev}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Back
        </button>
        <button
          onClick={() => navigateTo("download")}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Continue to Download
        </button>
      </div>
    </div>
  );
}
