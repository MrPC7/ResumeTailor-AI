"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Edit3, Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { analyzeJD } from "@/features/workflow/services/analyze-jd.service";
import type { AnalyzedJD } from "@/features/workflow/types/workflow.types";

const jdSchema = z.object({
  jobDescription: z
    .string()
    .min(50, "Enter at least 50 characters")
    .max(20000, "Maximum 20,000 characters"),
});

type FormValues = z.infer<typeof jdSchema>;

export function StepJD() {
  const storedJdData = useWorkflowStore((s) => s.jdData);
  const completeJD = useWorkflowStore((s) => s.completeJD);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const resume = useWorkflowStore((s) => s.uploadData?.resume);

  // If we have cached JD data, start in "review" mode; otherwise start in "edit" mode.
  const [mode, setMode] = useState<"edit" | "review">(storedJdData ? "review" : "edit");
  const [analyzedJD, setAnalyzedJD] = useState<AnalyzedJD | null>(storedJdData?.analyzedJD ?? null);
  const [jobDescriptionValue, setJobDescriptionValue] = useState(
    storedJdData?.jobDescription ?? "",
  );

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(jdSchema),
    defaultValues: { jobDescription: storedJdData?.jobDescription ?? "" },
  });

  const charCount = watch("jobDescription", storedJdData?.jobDescription ?? "").length;

  const mutation = useMutation({
    mutationFn: (values: FormValues) => analyzeJD(values.jobDescription),
    onSuccess: (data, variables) => {
      setAnalyzedJD(data);
      setJobDescriptionValue(variables.jobDescription);
      setMode("review");
    },
  });

  const onSubmit = (values: FormValues) => {
    // Avoid unnecessary API call if the JD text hasn't changed.
    if (
      storedJdData &&
      values.jobDescription.trim() === storedJdData.jobDescription.trim()
    ) {
      completeJD(storedJdData);
      return;
    }
    mutation.mutate(values);
  };

  const handleContinue = () => {
    if (analyzedJD) {
      completeJD({ jobDescription: jobDescriptionValue, analyzedJD });
    }
  };

  // ── Review mode (cached or freshly analyzed JD) ────────────────────────
  if (mode === "review" && analyzedJD) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Job Description Analyzed</CardTitle>
          <CardDescription>
            Targeting{" "}
            <span className="font-medium text-slate-900">{resume?.name ?? "your resume"}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3 rounded-md border border-emerald-200 bg-emerald-50 p-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              <p className="text-sm font-medium text-emerald-900">Job description analyzed</p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-emerald-800">
              <span>
                <span className="font-medium">Role:</span> {analyzedJD.role ?? "—"}
              </span>
              <span>
                <span className="font-medium">Seniority:</span> {analyzedJD.seniority ?? "—"}
              </span>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-emerald-800">
                Required skills ({analyzedJD.requiredSkills.length})
              </p>
              <div className="flex flex-wrap gap-1">
                {analyzedJD.requiredSkills.slice(0, 8).map((skill) => (
                  <Badge
                    key={skill}
                    variant="secondary"
                    className="bg-emerald-100 text-xs text-emerald-800"
                  >
                    {skill}
                  </Badge>
                ))}
                {analyzedJD.requiredSkills.length > 8 && (
                  <Badge variant="secondary" className="text-xs">
                    +{analyzedJD.requiredSkills.length - 8} more
                  </Badge>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={goPrev}>
                ← Previous
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="flex items-center gap-1.5"
                onClick={() => setMode("edit")}
              >
                <Edit3 className="h-3.5 w-3.5" />
                Edit JD
              </Button>
            </div>
            <Button onClick={handleContinue}>Continue to ATS Analysis →</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // ── Edit mode (new JD or editing existing) ─────────────────────────────
  return (
    <Card>
      <CardHeader>
        <CardTitle>Paste Job Description</CardTitle>
        <CardDescription>
          Copy and paste the full job posting for{" "}
          <span className="font-medium text-slate-900">{resume?.name ?? "your resume"}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-1.5">
            <Textarea
              {...register("jobDescription")}
              className="min-h-[200px] resize-none font-mono text-sm"
              placeholder="Paste the complete job description here including responsibilities, requirements, and qualifications..."
              disabled={mutation.isPending}
            />
            <div className="flex items-center justify-between">
              {errors.jobDescription ? (
                <p className="text-xs text-red-600">{errors.jobDescription.message}</p>
              ) : (
                <span />
              )}
              <p className="ml-auto text-xs text-slate-400">
                {charCount.toLocaleString()} / 20,000
              </p>
            </div>
          </div>

          {/* API error */}
          {mutation.isError && <p className="text-sm text-red-600">{mutation.error.message}</p>}

          <div className="flex items-center justify-between gap-3">
            <Button variant="outline" size="sm" type="button" onClick={goPrev}>
              ← Previous
            </Button>
            <Button className="flex-1" disabled={mutation.isPending} type="submit">
              {mutation.isPending ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing job description...
                </span>
              ) : (
                "Analyze Job Description"
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
