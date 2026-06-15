"use client";

import { useState } from "react";
import { Check, ClipboardCopy, Download, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ATSComparisonCard } from "@/components/ats/ATSComparisonCard";
import {
  downloadBlob,
  exportResume,
  type ExportFormat,
} from "@/features/workflow/services/export-resume.service";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { pushToast } from "@/lib/toast";

export function StepDownload() {
  const optimizeResult = useWorkflowStore((s) => s.optimizeResult!);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const reset = useWorkflowStore((s) => s.reset);

  const { customizedResume, atsComparison } = optimizeResult;
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
      {/* After score comparison */}
      <ATSComparisonCard comparison={atsComparison} />

      {/* Download options */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Download Your Optimized Resume</CardTitle>
          <CardDescription>
            Your resume for{" "}
            <span className="font-medium text-slate-900">
              {customizedResume.name ?? "you"}
            </span>{" "}
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

      {/* Navigation */}
      <div className="flex items-center justify-between gap-3">
        <Button variant="outline" size="sm" onClick={goPrev}>
          ← Preview
        </Button>
        <Button className="flex items-center gap-2" variant="ghost" onClick={reset}>
          <RotateCcw className="h-4 w-4" />
          Start Over
        </Button>
      </div>
    </div>
  );
}
