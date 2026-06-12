"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { analyzeJD } from "@/features/workflow/services/analyze-jd.service";
import type {
  AnalyzedJD,
  JDStepData,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";

const jdSchema = z.object({
  jobDescription: z
    .string()
    .min(50, "Enter at least 50 characters")
    .max(20000, "Maximum 20,000 characters"),
});

type FormValues = z.infer<typeof jdSchema>;

type Props = {
  resume: StructuredResume;
  onComplete: (data: JDStepData) => void;
};

export function StepJD({ resume, onComplete }: Props) {
  const [analyzedJD, setAnalyzedJD] = useState<AnalyzedJD | null>(null);
  const [jobDescription, setJobDescriptionValue] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(jdSchema) });

  const charCount = watch("jobDescription", "").length;

  const mutation = useMutation({
    mutationFn: (values: FormValues) => analyzeJD(values.jobDescription),
    onSuccess: (data, variables) => {
      setAnalyzedJD(data);
      setJobDescriptionValue(variables.jobDescription);
    },
  });

  const onSubmit = (values: FormValues) => {
    mutation.mutate(values);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Paste Job Description</CardTitle>
        <CardDescription>
          Copy and paste the full job posting for{" "}
          <span className="font-medium text-slate-900">{resume.name ?? "your resume"}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-1.5">
            <Textarea
              {...register("jobDescription")}
              className="min-h-[200px] resize-none font-mono text-sm"
              placeholder="Paste the complete job description here including responsibilities, requirements, and qualifications..."
              disabled={mutation.isPending || !!analyzedJD}
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

          {/* JD analysis result */}
          {analyzedJD && (
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
          )}

          {/* Actions */}
          {!analyzedJD ? (
            <Button className="w-full" disabled={mutation.isPending} type="submit">
              {mutation.isPending ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing job description...
                </span>
              ) : (
                "Analyze Job Description"
              )}
            </Button>
          ) : (
            <Button
              className="w-full"
              type="button"
              onClick={() => onComplete({ jobDescription, analyzedJD })}
            >
              Continue to Analysis →
            </Button>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
