"use client";

import { useState } from "react";
import { Check, ClipboardCopy, Download, FileText, RotateCcw, Search } from "lucide-react";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ATSComparisonCard } from "@/components/ats/ATSComparisonCard";
import { ATSBreakdown } from "@/components/ats/ATSBreakdown";
import { MatchedKeywords } from "@/components/ats/MatchedKeywords";
import { MissingKeywords } from "@/components/ats/MissingKeywords";
import { CoverLetterTab } from "@/components/cover-letter/CoverLetterTab";
import {
  downloadBlob,
  exportResume,
  type ExportFormat,
} from "@/features/workflow/services/export-resume.service";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { pushToast } from "@/lib/toast";

type TabId = "resume" | "ats" | "cover-letter";

const TABS: Array<{ id: TabId; label: string; icon: React.ReactNode }> = [
  { id: "resume", label: "Resume Preview", icon: <Download className="h-4 w-4" /> },
  { id: "ats", label: "ATS Insights", icon: <Search className="h-4 w-4" /> },
  { id: "cover-letter", label: "Cover Letter", icon: <FileText className="h-4 w-4" /> },
];

export function StepDownload() {
  const optimizeResult = useWorkflowStore((s) => s.optimizeResult!);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const reset = useWorkflowStore((s) => s.reset);

  const { customizedResume, atsComparison } = optimizeResult;
  const [activeTab, setActiveTab] = useState<TabId>("resume");
  const [copied, setCopied] = useState(false);
  const [isDownloading, setIsDownloading] = useState<ExportFormat | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownload = async (format: ExportFormat) => {
    try {
      setDownloadError(null);
      setIsDownloading(format);
      const result = await exportResume({
        resume: customizedResume,
        format,
        fileName: customizedResume.name ?? undefined,
      });
      downloadBlob(result.blob, result.fileName);
      pushToast({ type: "success", message: `${format.toUpperCase()} download started.` });
    } catch (error) {
      setDownloadError(error instanceof Error ? error.message : "Failed to export resume.");
    } finally {
      setIsDownloading(null);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(customizedResume, null, 2));
      setCopied(true);
      pushToast({ type: "success", message: "Optimized resume JSON copied to clipboard." });
      setTimeout(() => setCopied(false), 2000);
    } catch {
      pushToast({ type: "error", message: "Unable to copy JSON. Please try again." });
    }
  };

  return (
    <div className="space-y-6">
      {/* Score summary */}
      <ATSComparisonCard comparison={atsComparison} />

      {/* Tab bar */}
      <div className="flex gap-1 rounded-xl border border-slate-200 bg-slate-100 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
              activeTab === tab.id
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            {tab.icon}
            <span className="hidden sm:inline">{tab.label}</span>
            <span className="sm:hidden">
              {tab.id === "resume" ? "Resume" : tab.id === "ats" ? "ATS" : "Cover Letter"}
            </span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="min-h-[300px]">
        {/* ── Resume Download Tab ────────────────────────────────── */}
        {activeTab === "resume" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Download Your Optimized Resume</CardTitle>
              <CardDescription>
                Your resume for{" "}
                <span className="font-medium text-slate-900">{customizedResume.name ?? "you"}</span>{" "}
                is ready to download.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                className="w-full"
                onClick={() => void handleDownload("pdf")}
                disabled={isDownloading !== null}
              >
                <Download className="mr-2 h-4 w-4" />
                {isDownloading === "pdf" ? "Generating PDF..." : "Download PDF"}
              </Button>
              <Button
                className="w-full"
                variant="secondary"
                onClick={() => void handleDownload("docx")}
                disabled={isDownloading !== null}
              >
                <Download className="mr-2 h-4 w-4" />
                {isDownloading === "docx" ? "Generating DOCX..." : "Download DOCX"}
              </Button>
              <Button className="w-full" variant="outline" onClick={handleCopy}>
                {copied ? (
                  <>
                    <Check className="mr-2 h-4 w-4 text-emerald-600" />
                    <span className="text-emerald-600">Copied!</span>
                  </>
                ) : (
                  <>
                    <ClipboardCopy className="mr-2 h-4 w-4" />
                    Copy JSON to Clipboard
                  </>
                )}
              </Button>
              {downloadError && <p className="text-sm text-red-600">{downloadError}</p>}
            </CardContent>
          </Card>
        )}

        {/* ── ATS Insights Tab ───────────────────────────────────── */}
        {activeTab === "ats" && (
          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Optimized Score Breakdown</CardTitle>
                <CardDescription>Per-dimension scores after optimization.</CardDescription>
              </CardHeader>
              <CardContent>
                <ATSBreakdown scores={atsComparison.after.scores} />
              </CardContent>
            </Card>

            <div className="grid gap-4 sm:grid-cols-2">
              {atsComparison.after.matchedKeywords.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">
                      Matched Keywords ({atsComparison.after.matchedKeywords.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <MatchedKeywords keywords={atsComparison.after.matchedKeywords} />
                  </CardContent>
                </Card>
              )}
              {atsComparison.after.missingKeywords.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">
                      Still Missing ({atsComparison.after.missingKeywords.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <MissingKeywords keywords={atsComparison.after.missingKeywords} />
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* ── Cover Letter Tab ───────────────────────────────────── */}
        {activeTab === "cover-letter" && <CoverLetterTab />}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between gap-3">
        <Button variant="outline" size="sm" onClick={goPrev}>
          ← Previous
        </Button>
        <Button
          className="flex items-center gap-2"
          variant="ghost"
          onClick={() => {
            if (window.confirm("Start over? This will clear all your progress.")) {
              reset();
            }
          }}
        >
          <RotateCcw className="h-4 w-4" />
          Start Over
        </Button>
      </div>
    </div>
  );
}
