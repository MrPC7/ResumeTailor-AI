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
import type { OptimizeResult } from "@/features/workflow/types/workflow.types";

type Props = {
  optimizeResult: OptimizeResult;
  onReset: () => void;
};

export function StepDownload({ optimizeResult, onReset }: Props) {
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
    } catch (error) {
      setDownloadError(error instanceof Error ? error.message : "Failed to export resume.");
    } finally {
      setIsDownloading(null);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(customizedResume, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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

      {/* Reset */}
      <Button className="w-full" variant="ghost" onClick={onReset}>
        <RotateCcw className="mr-2 h-4 w-4" />
        Start Over with a Different Resume
      </Button>
    </div>
  );
}
