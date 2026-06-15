"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Check,
  ClipboardCopy,
  Download,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import {
  generateCoverLetter,
  type CoverLetterResult,
} from "@/features/workflow/services/cover-letter.service";
import {
  exportResume,
  downloadBlob,
} from "@/features/workflow/services/export-resume.service";
import { pushToast } from "@/lib/toast";

export function CoverLetterTab() {
  const resume = useWorkflowStore((s) => s.optimizeResult?.customizedResume ?? s.uploadData?.resume);
  const jdData = useWorkflowStore((s) => s.jdData);
  const coverLetter = useWorkflowStore((s) => s.coverLetter);
  const setCoverLetter = useWorkflowStore((s) => s.setCoverLetter);

  const [copied, setCopied] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!resume || !jdData) throw new Error("Resume and JD are required.");
      return generateCoverLetter(resume, jdData.analyzedJD);
    },
    onSuccess: (data: CoverLetterResult) => {
      setCoverLetter(data);
    },
  });

  const handleCopy = async () => {
    if (!coverLetter) return;
    try {
      await navigator.clipboard.writeText(coverLetter.coverLetter);
      setCopied(true);
      pushToast({ type: "success", message: "Cover letter copied to clipboard." });
      setTimeout(() => setCopied(false), 2000);
    } catch {
      pushToast({ type: "error", message: "Unable to copy. Please try again." });
    }
  };

  const handleDownloadTxt = () => {
    if (!coverLetter) return;
    const blob = new Blob([coverLetter.coverLetter], { type: "text/plain;charset=utf-8" });
    downloadBlob(blob, "cover_letter.txt");
    pushToast({ type: "success", message: "TXT download started." });
  };

  const handleDownloadPdf = async () => {
    if (!coverLetter || !resume) return;
    try {
      setIsDownloadingPdf(true);
      // Build a minimal "resume" with just the cover letter as summary
      // to reuse the existing export endpoint for PDF generation
      const coverLetterResume = {
        name: resume.name,
        email: resume.email,
        phone: resume.phone,
        summary: coverLetter.coverLetter,
        skills: [],
        experience: [],
        education: [],
        projects: [],
      };
      const result = await exportResume({
        resume: coverLetterResume,
        format: "pdf",
        fileName: `${resume.name ?? "cover_letter"}_cover_letter`,
      });
      downloadBlob(result.blob, result.fileName);
      pushToast({ type: "success", message: "PDF download started." });
    } catch (error) {
      pushToast({
        type: "error",
        message: error instanceof Error ? error.message : "Failed to export PDF.",
      });
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  // ── Not yet generated ─────────────────────────────────────────────────
  if (!coverLetter && !mutation.isPending) {
    return (
      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-violet-100 to-indigo-100">
            <FileText className="h-7 w-7 text-violet-600" />
          </div>
          <CardTitle>Generate Cover Letter</CardTitle>
          <CardDescription>
            Create a professional, job-specific cover letter using your resume and the analyzed job description.
            No information will be invented — only real skills and experience.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            className="w-full gap-2"
            onClick={() => mutation.mutate()}
            disabled={!resume || !jdData}
          >
            <Sparkles className="h-4 w-4" />
            Generate Cover Letter
          </Button>
          {mutation.isError && (
            <p className="text-sm text-red-600">{mutation.error.message}</p>
          )}
        </CardContent>
      </Card>
    );
  }

  // ── Generating ────────────────────────────────────────────────────────
  if (mutation.isPending) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center py-12">
          <Loader2 className="h-10 w-10 animate-spin text-violet-400" />
          <p className="mt-4 text-sm font-medium text-slate-700">
            Generating your cover letter...
          </p>
          <p className="mt-1 text-xs text-slate-400">
            This may take a few seconds
          </p>
        </CardContent>
      </Card>
    );
  }

  // ── Generated ─────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Cover letter text */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-violet-600" />
              Your Cover Letter
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-xs"
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Regenerate
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
              {coverLetter!.coverLetter}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Insights */}
      <div className="grid gap-4 sm:grid-cols-2">
        {coverLetter!.strengthsHighlighted.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Strengths Highlighted</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {coverLetter!.strengthsHighlighted.map((s, i) => (
                  <Badge key={i} variant="secondary" className="bg-violet-50 text-xs text-violet-700">
                    {s}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {coverLetter!.matchingSkillsUsed.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Matching Skills Used</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {coverLetter!.matchingSkillsUsed.map((s, i) => (
                  <Badge key={i} variant="secondary" className="bg-emerald-50 text-xs text-emerald-700">
                    {s}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <Separator />

      {/* Actions */}
      <div className="grid gap-2 sm:grid-cols-3">
        <Button variant="outline" className="gap-2" onClick={handleCopy}>
          {copied ? (
            <>
              <Check className="h-4 w-4 text-emerald-600" />
              <span className="text-emerald-600">Copied!</span>
            </>
          ) : (
            <>
              <ClipboardCopy className="h-4 w-4" />
              Copy Text
            </>
          )}
        </Button>
        <Button variant="outline" className="gap-2" onClick={handleDownloadTxt}>
          <Download className="h-4 w-4" />
          Download TXT
        </Button>
        <Button
          variant="outline"
          className="gap-2"
          onClick={() => void handleDownloadPdf()}
          disabled={isDownloadingPdf}
        >
          <Download className="h-4 w-4" />
          {isDownloadingPdf ? "Generating..." : "Download PDF"}
        </Button>
      </div>
    </div>
  );
}
