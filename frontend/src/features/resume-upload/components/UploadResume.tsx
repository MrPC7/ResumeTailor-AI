"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { FileText, Loader2, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  type UploadResumeFormValues,
  uploadResumeSchema,
} from "@/features/resume-upload/schemas/upload-resume.schema";
import { uploadResume } from "@/features/resume-upload/services/upload-resume.service";
import type { UploadedResume } from "@/features/resume-upload/types/upload.types";

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

export function UploadResume() {
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFile, setUploadedFile] = useState<UploadedResume | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const {
    handleSubmit,
    setValue,
    clearErrors,
    setError,
    formState: { errors },
  } = useForm<UploadResumeFormValues>({
    resolver: zodResolver(uploadResumeSchema),
  });

  const uploadMutation = useMutation({
    mutationFn: uploadResume,
    onSuccess: (data) => {
      setUploadedFile(data);
    },
    onError: (error) => {
      setError("file", { message: error.message });
    },
  });

  const applyFile = (file: File | undefined) => {
    if (!file) {
      return;
    }

    setSelectedFile(file);
    setUploadedFile(null);
    clearErrors("file");
    setValue("file", file, { shouldValidate: true, shouldTouch: true });
  };

  const onFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    applyFile(event.target.files?.[0]);
  };

  const onDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    applyFile(event.dataTransfer.files?.[0]);
  };

  const onSubmit = async (data: UploadResumeFormValues) => {
    await uploadMutation.mutateAsync(data.file);
  };

  const previewFile = uploadedFile
    ? {
        name: uploadedFile.fileName,
        size: uploadedFile.fileSize,
        type: uploadedFile.fileType,
      }
    : selectedFile
      ? {
          name: selectedFile.name,
          size: selectedFile.size,
          type: selectedFile.type || "unknown",
        }
      : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Upload Resume</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div
            className={`rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
              isDragActive ? "border-slate-900 bg-slate-100" : "border-slate-300"
            }`}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragActive(true);
            }}
            onDragLeave={() => setIsDragActive(false)}
            onDrop={onDrop}
          >
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
              <UploadCloud className="h-6 w-6 text-slate-700" />
            </div>
            <p className="text-sm font-medium text-slate-900">Drag and drop your resume here</p>
            <p className="mt-1 text-xs text-slate-500">PDF or DOCX, up to 10MB</p>
            <div className="mt-4 flex items-center justify-center gap-2">
              <Input
                ref={inputRef}
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                className="hidden"
                onChange={onFileChange}
                type="file"
              />
              <Button onClick={() => inputRef.current?.click()} type="button" variant="outline">
                Choose File
              </Button>
            </div>
          </div>

          {errors.file?.message ? (
            <p className="text-sm text-red-600">{errors.file.message}</p>
          ) : null}

          {previewFile ? (
            <div className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex items-start gap-3">
                <FileText className="mt-0.5 h-5 w-5 text-slate-700" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-slate-900">{previewFile.name}</p>
                  <p className="text-xs text-slate-600">Type: {previewFile.type}</p>
                  <p className="text-xs text-slate-600">Size: {formatFileSize(previewFile.size)}</p>
                </div>
              </div>
            </div>
          ) : null}

          <Button
            className="w-full"
            disabled={uploadMutation.isPending || !selectedFile}
            type="submit"
          >
            {uploadMutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Uploading...
              </span>
            ) : (
              "Upload Resume"
            )}
          </Button>

          {uploadedFile ? (
            <p className="text-sm text-emerald-700">
              Upload successful for {uploadedFile.fileName}.
            </p>
          ) : null}
        </form>
      </CardContent>
    </Card>
  );
}
