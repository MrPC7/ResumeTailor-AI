"use client";

import { StepATS } from "@/features/workflow/components/StepATS";
import { StepDownload } from "@/features/workflow/components/StepDownload";
import { StepJD } from "@/features/workflow/components/StepJD";
import { StepPreview } from "@/features/workflow/components/StepPreview";
import { StepRecommendations } from "@/features/workflow/components/StepRecommendations";
import { StepUpload } from "@/features/workflow/components/StepUpload";
import { WorkflowStepper } from "@/features/workflow/components/WorkflowStepper";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";

export default function Home() {
  const currentStep = useWorkflowStore((s) => s.currentStep);

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">ResumeTailor AI</h1>
          <p className="mt-2 text-sm text-slate-500">
            AI-powered resume tailoring for every job application
          </p>
        </header>

        {/* Stepper — self-contained, reads from store */}
        <WorkflowStepper />

        {/* Step content */}
        <div className="mt-8">
          {currentStep === "upload" && <StepUpload />}
          {currentStep === "jd" && <StepJD />}
          {currentStep === "ats" && <StepATS />}
          {currentStep === "recommendations" && <StepRecommendations />}
          {currentStep === "preview" && <StepPreview />}
          {currentStep === "download" && <StepDownload />}
        </div>
      </div>
    </main>
  );
}
