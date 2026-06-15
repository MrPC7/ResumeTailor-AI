"use client";

import { Check, Download, Eye, FileText, Search, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import type { WorkflowStep } from "@/features/workflow/types/workflow.types";

type Step = {
  id: WorkflowStep;
  label: string;
  icon: React.ReactNode;
};

const STEPS: Step[] = [
  { id: "upload", label: "Upload Resume", icon: <Upload className="h-4 w-4" /> },
  { id: "jd", label: "Job Description", icon: <FileText className="h-4 w-4" /> },
  { id: "optimize", label: "Optimize", icon: <Search className="h-4 w-4" /> },
  { id: "preview", label: "Preview", icon: <Eye className="h-4 w-4" /> },
  { id: "download", label: "Download", icon: <Download className="h-4 w-4" /> },
];

const STEP_ORDER: WorkflowStep[] = ["upload", "jd", "optimize", "preview", "download"];

type Props = { currentStep: WorkflowStep };

export function WorkflowStepper({ currentStep }: Props) {
  const currentIndex = STEP_ORDER.indexOf(currentStep);

  return (
    <nav aria-label="Workflow progress">
      {/* Desktop stepper */}
      <div className="hidden sm:block">
        <div className="rounded-xl border border-slate-200 bg-white px-6 py-4 shadow-sm">
          <ol className="flex w-full items-center">
            {STEPS.map((step, index) => {
              const isCompleted = index < currentIndex;
              const isActive = index === currentIndex;
              const isLast = index === STEPS.length - 1;

              return (
                <li
                  key={step.id}
                  className={cn("flex items-center", isLast ? "flex-none" : "flex-1")}
                >
                  <div className="flex flex-col items-center gap-1.5">
                    <div
                      className={cn(
                        "flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-medium transition-all duration-200",
                        isCompleted &&
                          "border-emerald-600 bg-emerald-600 text-white shadow-sm shadow-emerald-200",
                        isActive &&
                          "border-slate-900 bg-slate-900 text-white shadow-sm shadow-slate-300",
                        !isCompleted && !isActive && "border-slate-200 bg-slate-50 text-slate-400"
                      )}
                    >
                      {isCompleted ? <Check className="h-4 w-4" /> : step.icon}
                    </div>
                    <span
                      className={cn(
                        "whitespace-nowrap text-xs font-medium transition-colors",
                        isCompleted && "text-emerald-700",
                        isActive && "text-slate-900",
                        !isCompleted && !isActive && "text-slate-400"
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
                          isCompleted ? "bg-emerald-500" : "bg-slate-200"
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

      {/* Mobile: compact progress bar */}
      <div className="sm:hidden">
        <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-white">
              {STEPS[currentIndex]?.icon}
            </div>
            <span className="text-sm font-semibold text-slate-900">
              {STEPS[currentIndex]?.label}
            </span>
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
      </div>
    </nav>
  );
}
