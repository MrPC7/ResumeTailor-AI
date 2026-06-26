"use client";

import { cn } from "@/lib/utils";

type Props = {
  before: string;
  after: string;
};

function matchLevelLabel(level: string): string {
  return level.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function matchLevelColor(level: string): string {
  switch (level) {
    case "strong_match":
      return "text-emerald-700 bg-emerald-100";
    case "good_match":
      return "text-amber-700 bg-amber-100";
    case "partial_match":
      return "text-orange-700 bg-orange-100";
    case "weak_match":
      return "text-red-700 bg-red-100";
    case "no_match":
      return "text-slate-700 bg-slate-100";
    default:
      return "text-slate-700 bg-slate-100";
  }
}

export function ComparisonMatchLevel({ before, after }: Props) {
  const changed = before !== after;

  return (
    <div
      className="rounded-lg border bg-card p-4 shadow-sm"
      aria-label={`Match level changed from ${matchLevelLabel(before)} to ${matchLevelLabel(after)}`}
    >
      <h3 className="text-sm font-medium text-muted-foreground">Match Level</h3>
      <div className="mt-3 flex items-center justify-center gap-3">
        <span
          className={cn("rounded-full px-3 py-1 text-sm font-semibold", matchLevelColor(before))}
        >
          {matchLevelLabel(before)}
        </span>

        <span
          className={cn("text-lg", changed ? "text-emerald-600" : "text-slate-400")}
          aria-hidden="true"
        >
          â†’
        </span>

        <span
          className={cn("rounded-full px-3 py-1 text-sm font-semibold", matchLevelColor(after))}
        >
          {matchLevelLabel(after)}
        </span>

        {changed && <span className="ml-2 text-xs font-medium text-emerald-600">â†‘ Improved</span>}
      </div>
    </div>
  );
}
