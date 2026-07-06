"use client";

import { useState } from "react";
import { Download, FileText, Loader2, RotateCcw } from "lucide-react";
import { CoverLetterTab } from "@/components/cover-letter/CoverLetterTab";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { exportResume, downloadBlob } from "@/features/workflow/services/export-resume.service";
import { pushToast } from "@/lib/toast";
import { cn } from "@/lib/utils";

type TabId = "resume" | "cover-letter";

export function StepDownload() {
  const uploadData = useWorkflowStore((s) => s.uploadData!);
  const previewData = useWorkflowStore((s) => s.previewData);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const navigateTo = useWorkflowStore((s) => s.navigateTo);
  const reset = useWorkflowStore((s) => s.reset);

  const [activeTab, setActiveTab] = useState<TabId>("resume");
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportingDocx, setExportingDocx] = useState(false);

  const customizedResume = previewData?.customizedResume ?? uploadData.resume;
  const resumeName = uploadData.resume.name ?? "resume";

  const handleExport = async (format: "pdf" | "docx") => {
    const setExporting = format === "pdf" ? setExportingPdf : setExportingDocx;
    setExporting(true);
    try {
      const result = await exportResume({
        resume: customizedResume,
        format,
        fileName: `${resumeName}_optimized`,
      });
      downloadBlob(result.blob, result.fileName);
      pushToast({ type: "success", message: `${format.toUpperCase()} download started.` });
    } catch {
      // Error toast already handled by exportResume
    } finally {
      setExporting(false);
    }
  };

  const tabs: { id: TabId; label: string }[] = [
    { id: "resume", label: "Optimized Resume" },
    { id: "cover-letter", label: "Cover Letter" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-center">
        <p className="text-sm font-medium text-emerald-700">
          ✓ Your resume is ready — download below
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 rounded-lg border bg-white p-1" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            id={`dl-tab-${tab.id}`}
            aria-controls={`dl-tabpanel-${tab.id}`}
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
      <div role="tabpanel" id={`dl-tabpanel-${activeTab}`} aria-labelledby={`dl-tab-${activeTab}`}>
        {activeTab === "resume" && (
          <div className="space-y-4">
            {/* Resume preview card */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100">
                  <FileText className="h-5 w-5 text-indigo-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-slate-900">{resumeName} — Optimized</p>
                  <p className="text-xs text-slate-500">
                    {customizedResume.skills.length} skills
                    {customizedResume.experience.length > 0 &&
                      ` · ${customizedResume.experience.length} experience entries`}
                    {customizedResume.projects.length > 0 &&
                      ` · ${customizedResume.projects.length} projects`}
                  </p>
                </div>
              </div>
            </div>

            {/* Download buttons */}
            <div className="grid gap-3 sm:grid-cols-2">
              <button
                onClick={() => void handleExport("pdf")}
                disabled={exportingPdf}
                className="flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {exportingPdf ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                {exportingPdf ? "Generating PDF..." : "Download PDF"}
              </button>
              <button
                onClick={() => void handleExport("docx")}
                disabled={exportingDocx}
                className="flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {exportingDocx ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                {exportingDocx ? "Generating DOCX..." : "Download DOCX"}
              </button>
            </div>
          </div>
        )}

        {activeTab === "cover-letter" && <CoverLetterTab />}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={goPrev}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          ← Back
        </button>
        <div className="flex gap-3">
          <button
            onClick={() => navigateTo("recruiter")}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            View Recruiter Review
          </button>
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            <RotateCcw className="h-4 w-4" />
            Start New
          </button>
        </div>
      </div>
    </div>
  );
}
