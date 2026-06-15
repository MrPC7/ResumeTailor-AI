"use client";

import { Check, Download, Eye, FileText, Search, Settings, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { STEP_ORDER, useWorkflowStore } from "@/features/workflow/store/workflow.store";
import type { WorkflowStep } from "@/features/workflow/types/workflow.types";

type StepMeta = {
  id: WorkflowStep;
  label: string;
  shortLabel: string;
  icon: React.ReactNode;
};

const STEPS: StepMeta[] = [
  { id: "upload", label: "Upload Resume", shortLabel: "Upload", icon: <Upload className="h-4 w-4" /> },
  { id: "jd", label: "Job Description", shortLabel: "Job", icon: <FileText className="h-4 w-4" /> },
  { id: "ats", label: "ATS Analysis", shortLabel: "ATS", icon: <Search className="h-4 w-4" /> },
  { id: "recommendations", label: "Recommendations", shortLabel: "Recs", icon: <Settings className="h-4 w-4" /> },
  { id: "preview", label: "Preview", shortLabel: "Preview", icon: <Eye className="h-4 w-4" /> },
  { id: "download", label: "Download", shortLabel: "Download", icon: <Download className="h-4 w-4" /> },
];

export function WorkflowStepper() {
  const currentStep = useWorkflowStore((s) => s.currentStep);
  const canNavigateTo = useWorkflowStore((s) => s.canNavigateTo);
  const isCompleted = useWorkflowStore((s) => s.isCompleted);
  const navigateTo = useWorkflowStore((s) => s.navigateTo);

  const currentIndex = STEP_ORDER.indexOf(currentStep);

  return (
    <nav aria-label="Workflow progress">
      {/* Desktop stepper */}
      <div className="hidden sm:block">
        <div className="rounded-xl border border-slate-200 bg-white px-6 py-4 shadow-sm">
          <ol className="flex w-full items-center">
            {STEPS.map((step, index) => {
              const completed = isCompleted(step.id);
              const isActive = step.id === currentStep;
              const reachable = canNavigateTo(step.id);
              const isLast = index === STEPS.length - 1;

              return (
                <li
                  key={step.id}
                  className={cn("flex items-center", isLast ? "flex-none" : "flex-1")}
                >
                  <div className="flex flex-col items-center gap-1.5">
                    <button
                      type="button"
                      disabled={!reachable}
                      onClick={() => navigateTo(step.id)}
                      aria-current={isActive ? "step" : undefined}
                      className={cn(
                        "flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-medium transition-all duration-200",
                        completed &&
                          "border-emerald-600 bg-emerald-600 text-white shadow-sm shadow-emerald-200",
                        isActive &&
                          "border-slate-900 bg-slate-900 text-white shadow-sm shadow-slate-300",
                        !completed && !isActive && reachable &&
                          "cursor-pointer border-slate-400 bg-slate-50 text-slate-600 hover:border-slate-600",
                        !completed && !isActive && !reachable &&
                          "cursor-not-allowed border-slate-200 bg-slate-50 text-slate-300",
                      )}
                    >
                      {completed && !isActive ? <Check className="h-4 w-4" /> : step.icon}
                    </button>
                    <span
                      className={cn(
                        "whitespace-nowrap text-xs font-medium transition-colors",
                        completed && !isActive && "text-emerald-700",
                        isActive && "text-slate-900",
                        !completed && !isActive && reachable && "text-slate-500",
                        !completed && !isActive && !reachable && "text-slate-300",
                      )}
                    >
                      {step.label}
                    </span>
                  </div>

                  {!isLast && (
                    <div className="mx-3 mt-[-18px] h-0.5 flex-1">
                      <div
                        className={cn(
                          "h-full rounded-full transition-colors duration-300",
                          completed ? "bg-emerald-500" : "bg-slate-200",
                        )}
                      />
                    </div>
                  )}
                </li>
              );
            })}
          </ol>
        </div>
      </div>

      {/* Mobile: compact pill + progress bar */}
      <div className="sm:hidden">
        <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-white">
              {STEPS[currentIndex]?.icon}
            </div>
            <div>
              <span className="text-sm font-semibold text-slate-900">
                {STEPS[currentIndex]?.label}
              </span>
            </div>
          </div>
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
            {currentIndex + 1} / {STEPS.length}
          </span>
        </div>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-slate-900 transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / STEPS.length) * 100}%` }}
          />
        </div>
        {/* Mobile step dots */}
        <div className="mt-3 flex justify-center gap-2">
          {STEPS.map((step) => {
            const completed = isCompleted(step.id);
            const isActive = step.id === currentStep;
            const reachable = canNavigateTo(step.id);
            return (
              <button
                key={step.id}
                type="button"
                disabled={!reachable}
                onClick={() => navigateTo(step.id)}
                aria-label={step.label}
                className={cn(
                  "h-2 rounded-full transition-all duration-200",
                  isActive && "w-6 bg-slate-900",
                  completed && !isActive && "w-2 cursor-pointer bg-emerald-500",
                  !completed && !isActive && reachable && "w-2 cursor-pointer bg-slate-300",
                  !completed && !isActive && !reachable && "w-2 cursor-not-allowed bg-slate-200",
                )}
              />
            );
          })}
        </div>
      </div>
    </nav>
  );
}
