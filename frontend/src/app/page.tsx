"use client";

import { StepAnalyze } from "@/features/workflow/components/StepAnalyze";
import { StepDownload } from "@/features/workflow/components/StepDownload";
import { StepJD } from "@/features/workflow/components/StepJD";
import { StepPreview } from "@/features/workflow/components/StepPreview";
import { StepUpload } from "@/features/workflow/components/StepUpload";
import { WorkflowStepper } from "@/features/workflow/components/WorkflowStepper";
import { useWorkflow } from "@/features/workflow/hooks/use-workflow";

export default function Home() {
  const workflow = useWorkflow();

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

        {/* Step indicator */}
        <WorkflowStepper currentStep={workflow.step} />

        {/* Step content */}
        <div className="mt-8">
          {workflow.step === "upload" && <StepUpload onComplete={workflow.completeUpload} />}

          {workflow.step === "jd" && workflow.uploadData && (
            <StepJD resume={workflow.uploadData.resume} onComplete={workflow.completeJD} />
          )}

          {workflow.step === "analyze" && workflow.uploadData && workflow.jdData && (
            <StepAnalyze
              resume={workflow.uploadData.resume}
              analyzedJD={workflow.jdData.analyzedJD}
              onComplete={workflow.completeAnalysis}
            />
          )}

          {workflow.step === "preview" &&
            workflow.uploadData &&
            workflow.jdData &&
            workflow.analysisResult && (
              <StepPreview
                resume={workflow.uploadData.resume}
                analyzedJD={workflow.jdData.analyzedJD}
                analysisResult={workflow.analysisResult}
                onContinue={workflow.goToDownload}
                onReset={workflow.reset}
              />
            )}

          {workflow.step === "download" && workflow.analysisResult && (
            <StepDownload analysisResult={workflow.analysisResult} onReset={workflow.reset} />
          )}
        </div>
      </div>
    </main>
  );
}
