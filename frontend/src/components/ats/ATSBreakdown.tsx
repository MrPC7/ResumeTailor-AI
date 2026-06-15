"use client";

import { cn } from "@/lib/utils";
import type { ATSScores } from "@/features/workflow/types/workflow.types";

type Props = {
  scores: ATSScores;
};

type BarItem = {
  label: string;
  value: number;
  weight: string;
};

function barColor(value: number): string {
  if (value >= 80) return "bg-emerald-500";
  if (value >= 60) return "bg-amber-500";
  return "bg-red-500";
}

function textColor(value: number): string {
  if (value >= 80) return "text-emerald-600";
  if (value >= 60) return "text-amber-600";
  return "text-red-600";
}

function ScoreBar({ label, value, weight }: BarItem) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-700">{label}</span>
          <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">
            {weight}
          </span>
        </div>
        <span className={cn("font-bold tabular-nums", textColor(value))}>{value}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-700 ease-out",
            barColor(value)
          )}
          style={{ width: `${value}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}

export function ATSBreakdown({ scores }: Props) {
  const items: BarItem[] = [
    { label: "Skills Match", value: scores.skills, weight: "30%" },
    { label: "Keyword Coverage", value: scores.keywords, weight: "25%" },
    { label: "Experience Fit", value: scores.experience, weight: "25%" },
    { label: "Education", value: scores.education, weight: "10%" },
    { label: "Overall Fit", value: scores.overallFit, weight: "10%" },
  ];

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <ScoreBar key={item.label} {...item} />
      ))}
    </div>
  );
}
