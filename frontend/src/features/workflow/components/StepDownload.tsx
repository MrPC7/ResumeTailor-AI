"use client";

import { useState } from "react";
import { Check, ClipboardCopy, Download, RotateCcw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  downloadBlob,
  exportResume,
  type ExportFormat,
} from "@/features/workflow/services/export-resume.service";
import type { AnalysisResult } from "@/features/workflow/types/workflow.types";
import { cn } from "@/lib/utils";

type Props = {
  analysisResult: AnalysisResult;
  onReset: () => void;
};

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-red-600";
}

export function StepDownload({ analysisResult, onReset }: Props) {
  const { matchScore, gapAnalysis, customizedResume } = analysisResult;
  const [copied, setCopied] = useState(false);
  const [isDownloading, setIsDownloading] = useState<ExportFormat | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const jsonString = JSON.stringify(customizedResume, null, 2);

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
    await navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Summary card */}
      <Card>
        <CardHeader>
          <CardTitle>Resume Ready</CardTitle>
          <CardDescription>
            Your resume has been customized for{" "}
            <span className="font-medium text-slate-900">{customizedResume.name ?? "you"}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Score summary */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "ATS Score", value: matchScore.score },
              { label: "Skills", value: matchScore.skillScore },
              { label: "Keywords", value: matchScore.keywordScore },
              { label: "Experience", value: matchScore.experienceScore },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-center"
              >
                <p className={cn("text-2xl font-bold tabular-nums", scoreColor(item.value))}>
                  {item.value}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">{item.label}</p>
              </div>
            ))}
          </div>

          <Separator />

          {/* Skill summary */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="mb-1.5 text-xs font-medium text-slate-500">
                Matched ({gapAnalysis.matchedSkills.length})
              </p>
              <div className="flex flex-wrap gap-1">
                {gapAnalysis.matchedSkills.slice(0, 6).map((s) => (
                  <Badge
                    key={s}
                    className="bg-emerald-100 text-xs text-emerald-800 hover:bg-emerald-100"
                  >
                    {s}
                  </Badge>
                ))}
                {gapAnalysis.matchedSkills.length > 6 && (
                  <Badge variant="secondary" className="text-xs">
                    +{gapAnalysis.matchedSkills.length - 6}
                  </Badge>
                )}
              </div>
            </div>
            <div>
              <p className="mb-1.5 text-xs font-medium text-slate-500">
                Missing ({gapAnalysis.missingSkills.length})
              </p>
              <div className="flex flex-wrap gap-1">
                {gapAnalysis.missingSkills.slice(0, 6).map((s) => (
                  <Badge key={s} className="bg-red-100 text-xs text-red-800 hover:bg-red-100">
                    {s}
                  </Badge>
                ))}
                {gapAnalysis.missingSkills.length === 0 && (
                  <p className="text-xs text-emerald-600">No gaps!</p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Download options */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Download Customized Resume</CardTitle>
          <CardDescription>Download your tailored resume in professional formats</CardDescription>
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
                Copy to Clipboard
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
