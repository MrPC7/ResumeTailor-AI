"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, FileText, Loader2, RefreshCw, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  type UploadResumeFormValues,
  uploadResumeSchema,
} from "@/features/resume-upload/schemas/upload-resume.schema";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { extractResume } from "@/features/workflow/services/extract-resume.service";
import { parseResume } from "@/features/workflow/services/parse-resume.service";
import type { UploadStepData } from "@/features/workflow/types/workflow.types";
import { cn } from "@/lib/utils";
import { pushToast } from "@/lib/toast";

type Phase = "idle" | "parsing" | "extracting" | "validating" | "done";

const PHASE_LABEL: Record<Phase, string> = {
  idle: "",
  parsing: "Parsing document...",
  extracting: "Extracting resume structure...",
  validating: "Validating resume content...",
  done: "Resume ready",
};

function toUserFriendlyError(message: string): string {
  const lower = message.toLowerCase();

  if (lower.includes("api_key_invalid") || lower.includes("api key not valid")) {
    return "AI service is not configured correctly. Please update a valid Gemini API key in backend .env.";
  }

  if (lower.includes("gemini_api_key is not configured")) {
    return "Gemini API key is missing. Add GEMINI_API_KEY in backend .env and restart the backend.";
  }

  if (lower.includes("service unavailable") || lower.includes("quota")) {
    return "AI service is temporarily unavailable. Please try again in a moment.";
  }

  // Resume validation rejection messages — pass through as-is
  if (
    lower.includes("does not appear to be a resume") ||
    lower.includes("could not identify common resume sections")
  ) {
    return message;
  }

  return "Failed to parse and extract resume. Please try again.";
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export function StepUpload() {
  const storedUploadData = useWorkflowStore((s) => s.uploadData);
  const completeUpload = useWorkflowStore((s) => s.completeUpload);

  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [freshUploadData, setFreshUploadData] = useState<UploadStepData | null>(null);
  const [showUploader, setShowUploader] = useState(!storedUploadData);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const {
    handleSubmit,
    setValue,
    clearErrors,
    setError,
    reset: resetForm,
    formState: { errors },
  } = useForm<UploadResumeFormValues>({ resolver: zodResolver(uploadResumeSchema) });

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      setPhase("parsing");
      const { rawText } = await parseResume(file);

      setPhase("extracting");
      const resume = await extractResume(rawText);

      // If we reach here, the backend validated it's a real resume
      return { rawText, resume };
    },
    onSuccess: (data) => {
      setPhase("done");
      setFreshUploadData(data);
    },
    onError: (error) => {
      setPhase("idle");
      const msg = toUserFriendlyError(error.message);
      setError("file", { message: msg });

      // Show toast for resume validation rejections
      if (
        error.message.toLowerCase().includes("does not appear to be a resume") ||
        error.message.toLowerCase().includes("could not identify common resume sections")
      ) {
        pushToast({ type: "error", message: msg });
      }
    },
  });

  const applyFile = (file: File | undefined) => {
    if (!file) return;
    setSelectedFile(file);
    setFreshUploadData(null);
    setPhase("idle");
    clearErrors("file");
    setValue("file", file, { shouldValidate: true, shouldTouch: true });
  };

  const onSubmit = (data: UploadResumeFormValues) => {
    mutation.mutate(data.file);
  };

  const handleContinueWithStored = () => {
    if (storedUploadData) completeUpload(storedUploadData);
  };

  const handleContinueWithFresh = () => {
    if (freshUploadData) completeUpload(freshUploadData);
  };

  const handleUploadDifferent = () => {
    setShowUploader(true);
    setFreshUploadData(null);
    setSelectedFile(null);
    setPhase("idle");
    resetForm();
  };

  const isPending = phase === "parsing" || phase === "extracting" || phase === "validating";

  // ── Cached resume: show summary with option to re-upload ──────────────
  if (storedUploadData && !showUploader) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Resume Uploaded</CardTitle>
          <CardDescription>Your resume has already been parsed and is ready to use.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3 rounded-md border border-emerald-200 bg-emerald-50 p-4">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
            <div className="space-y-1">
              <p className="text-sm font-semibold text-emerald-900">
                {storedUploadData.resume.name ?? "Resume"} — parsed successfully
              </p>
              <p className="text-xs text-emerald-700">
                {storedUploadData.resume.skills.length} skills ·{" "}
                {storedUploadData.resume.experience.length} positions ·{" "}
                {storedUploadData.resume.education.length} degrees
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row">
            <Button className="flex-1" onClick={handleContinueWithStored}>
              Continue with this resume →
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={handleUploadDifferent}
            >
              <RefreshCw className="h-4 w-4" />
              Upload a different resume
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // ── Upload form ────────────────────────────────────────────────────────
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Your Resume</CardTitle>
        <CardDescription>PDF or DOCX, up to 10MB</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          {/* Drop zone */}
          <div
            className={cn(
              "cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors",
              isDragActive
                ? "border-slate-900 bg-slate-50"
                : "border-slate-300 hover:border-slate-400 hover:bg-slate-50/50",
              freshUploadData && "border-emerald-400 bg-emerald-50",
            )}
            onClick={() => !isPending && inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragActive(true);
            }}
            onDragLeave={() => setIsDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragActive(false);
              applyFile(e.dataTransfer.files?.[0]);
            }}
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
              <UploadCloud className="h-6 w-6 text-slate-700" />
            </div>
            <p className="text-sm font-medium text-slate-900">Drag and drop your resume here</p>
            <p className="mt-1 text-xs text-slate-500">or click to browse</p>
            <input
              ref={inputRef}
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              onChange={(e) => applyFile(e.target.files?.[0])}
              type="file"
            />
          </div>

          {/* Validation error */}
          {errors.file?.message && (
            <div className="flex items-start gap-3 rounded-md border border-red-200 bg-red-50 p-3">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
              <p className="text-sm text-red-800">{errors.file.message}</p>
            </div>
          )}

          {/* Selected file info */}
          {selectedFile && !errors.file && (
            <div className="flex items-center gap-3 rounded-md border border-slate-200 bg-white p-3">
              <FileText className="h-5 w-5 shrink-0 text-slate-500" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-900">{selectedFile.name}</p>
                <p className="text-xs text-slate-500">{formatFileSize(selectedFile.size)}</p>
              </div>
            </div>
          )}

          {/* Phase progress */}
          {isPending && (
            <div className="flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2.5">
              <Loader2 className="h-4 w-4 shrink-0 animate-spin text-slate-600" />
              <p className="text-sm text-slate-700">{PHASE_LABEL[phase]}</p>
            </div>
          )}

          {/* Success state */}
          {freshUploadData && (
            <div className="flex items-start gap-3 rounded-md border border-emerald-200 bg-emerald-50 p-3">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
              <div className="space-y-0.5">
                <p className="text-sm font-medium text-emerald-900">
                  {freshUploadData.resume.name ?? "Resume"} parsed successfully
                </p>
                <p className="text-xs text-emerald-700">
                  {freshUploadData.resume.skills.length} skills ·{" "}
                  {freshUploadData.resume.experience.length} positions ·{" "}
                  {freshUploadData.resume.education.length} degrees
                </p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col gap-2">
            {!freshUploadData ? (
              <Button className="w-full" disabled={isPending || !selectedFile} type="submit">
                {isPending ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {PHASE_LABEL[phase]}
                  </span>
                ) : (
                  "Upload & Parse Resume"
                )}
              </Button>
            ) : (
              <Button className="w-full" onClick={handleContinueWithFresh} type="button">
                Continue to Job Description →
              </Button>
            )}
            {storedUploadData && (
              <Button
                variant="ghost"
                size="sm"
                type="button"
                onClick={() => setShowUploader(false)}
              >
                ← Back to saved resume
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
