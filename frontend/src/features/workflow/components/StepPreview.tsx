"use client";

import { useState } from "react";
import { RecruiterDashboard } from "@/components/recruiter";
import { ResumeView } from "@/components/resume/ResumeView";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { cn } from "@/lib/utils";

type TabId = "evaluation" | "resume";

export function StepPreview() {
  const uploadData = useWorkflowStore((s) => s.uploadData!);
  const recruiterData = useWorkflowStore((s) => s.recruiterData!);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const navigateTo = useWorkflowStore((s) => s.navigateTo);

  const [activeTab, setActiveTab] = useState<TabId>("evaluation");

  return (
    <div className="space-y-6">
      {/* Tab bar */}
      <div className="flex gap-1 rounded-lg border bg-white p-1" role="tablist">
        {(
          [
            { id: "evaluation", label: "Recruiter Evaluation" },
            { id: "resume", label: "Your Resume" },
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
      {activeTab === "evaluation" && <RecruiterDashboard evaluation={recruiterData.evaluation} />}
      {activeTab === "resume" && <ResumeView resume={uploadData.resume} />}

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
