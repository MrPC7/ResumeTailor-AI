"use client";

import { useState } from "react";
import { Download, Eye, GitCompare, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ResumeView } from "@/components/resume/ResumeView";
import { ResumeDiff } from "@/components/resume/ResumeDiff";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";

// ── Tab types ─────────────────────────────────────────────────────────────

type TabId = "original" | "customized" | "changes";

const TABS: Array<{ id: TabId; label: string; icon: React.ReactNode }> = [
  { id: "original", label: "Original Resume", icon: <FileText className="h-4 w-4" /> },
  { id: "customized", label: "Customized Resume", icon: <Eye className="h-4 w-4" /> },
  { id: "changes", label: "Changes", icon: <GitCompare className="h-4 w-4" /> },
];

// ── Score pill ────────────────────────────────────────────────────────────

function ScorePill({
  label,
  score,
  variant,
}: {
  label: string;
  score: number;
  variant: "neutral" | "after";
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-0.5 rounded-lg border px-4 py-2 text-center",
        variant === "after"
          ? "border-emerald-200 bg-emerald-50"
          : "border-slate-200 bg-slate-50",
      )}
    >
      <span
        className={cn(
          "text-2xl font-extrabold tabular-nums",
          variant === "after" ? "text-emerald-700" : "text-slate-700",
        )}
      >
        {score}
      </span>
      <span className="text-[11px] font-medium text-slate-400">{label}</span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────

export function StepPreview() {
  const originalResume = useWorkflowStore((s) => s.uploadData!.resume);
  const optimizeResult = useWorkflowStore((s) => s.optimizeResult!);
  const completePreview = useWorkflowStore((s) => s.completePreview);
  const goPrev = useWorkflowStore((s) => s.goPrev);

  const [activeTab, setActiveTab] = useState<TabId>("customized");
  const { customizedResume, atsComparison } = optimizeResult;
  const delta = atsComparison.afterScore - atsComparison.beforeScore;

  return (
    <div className="space-y-6">
      {/* ── Score summary bar ─────────────────────────────────── */}
      <div className="rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-semibold text-slate-900">Resume Preview</h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Review your optimized resume before downloading.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ScorePill label="Before" score={atsComparison.beforeScore} variant="neutral" />
            <div className="flex flex-col items-center px-1">
              <span
                className={cn(
                  "text-lg font-bold",
                  delta > 0 ? "text-emerald-600" : "text-slate-400",
                )}
              >
                {delta > 0 ? `+${delta}` : delta === 0 ? "±0" : delta}
              </span>
              <span className="text-[10px] text-slate-400">pts</span>
            </div>
            <ScorePill label="After" score={atsComparison.afterScore} variant="after" />
          </div>
        </div>
      </div>

      {/* ── Tab bar ──────────────────────────────────────────────── */}
      <div className="flex gap-1 rounded-xl border border-slate-200 bg-slate-100 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
              activeTab === tab.id
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-700",
            )}
          >
            {tab.icon}
            <span className="hidden sm:inline">{tab.label}</span>
            <span className="sm:hidden">
              {tab.id === "original" ? "Original" : tab.id === "customized" ? "Optimized" : "Changes"}
            </span>
          </button>
        ))}
      </div>

      {/* ── Tab content ──────────────────────────────────────────── */}
      <div className="min-h-[400px]">
        {activeTab === "original" && (
          <div>
            <p className="mb-4 text-xs font-medium uppercase tracking-wide text-slate-400">
              Your original resume
            </p>
            <ResumeView resume={originalResume} />
          </div>
        )}

        {activeTab === "customized" && (
          <div>
            <p className="mb-4 text-xs font-medium uppercase tracking-wide text-slate-400">
              Your AI-optimized resume
            </p>
            <ResumeView resume={customizedResume} />
          </div>
        )}

        {activeTab === "changes" && (
          <div>
            <p className="mb-4 text-xs font-medium uppercase tracking-wide text-slate-400">
              What changed between original and optimized
            </p>
            <ResumeDiff original={originalResume} customized={customizedResume} />
          </div>
        )}
      </div>

      {/* ── Actions ──────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3 border-t border-slate-100 pt-4">
        <Button variant="outline" size="sm" onClick={goPrev}>
          ← Previous
        </Button>
        <Button onClick={completePreview} className="gap-2">
          <Download className="h-4 w-4" />
          Proceed to Download
        </Button>
      </div>
    </div>
  );
}
