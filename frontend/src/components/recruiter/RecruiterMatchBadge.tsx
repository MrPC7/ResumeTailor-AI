"use client";

import { cn } from "@/lib/utils";

type Props = {
  matchLevel: string;
};

type MatchConfig = {
  label: string;
  bgClass: string;
  textClass: string;
  dotClass: string;
};

function getMatchConfig(level: string): MatchConfig {
  switch (level) {
    case "strong_match":
      return {
        label: "Strong Match",
        bgClass: "bg-emerald-50 border-emerald-200",
        textClass: "text-emerald-700",
        dotClass: "bg-emerald-500",
      };
    case "good_match":
      return {
        label: "Good Match",
        bgClass: "bg-amber-50 border-amber-200",
        textClass: "text-amber-700",
        dotClass: "bg-amber-500",
      };
    case "partial_match":
      return {
        label: "Partial Match",
        bgClass: "bg-orange-50 border-orange-200",
        textClass: "text-orange-700",
        dotClass: "bg-orange-500",
      };
    case "weak_match":
      return {
        label: "Weak Match",
        bgClass: "bg-red-50 border-red-200",
        textClass: "text-red-700",
        dotClass: "bg-red-500",
      };
    case "no_match":
      return {
        label: "No Match",
        bgClass: "bg-slate-50 border-slate-200",
        textClass: "text-slate-700",
        dotClass: "bg-slate-500",
      };
    default:
      return {
        label: level.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        bgClass: "bg-slate-50 border-slate-200",
        textClass: "text-slate-700",
        dotClass: "bg-slate-500",
      };
  }
}

export function RecruiterMatchBadge({ matchLevel }: Props) {
  const config = getMatchConfig(matchLevel);

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border p-4 shadow-sm",
        config.bgClass
      )}
      aria-label={`Match Level: ${config.label}`}
    >
      <p className="text-xs font-medium text-muted-foreground">Match Level</p>
      <div className="mt-2 flex items-center gap-2">
        <span
          className={cn("h-3 w-3 rounded-full", config.dotClass)}
          aria-hidden="true"
        />
        <span className={cn("text-lg font-bold", config.textClass)}>
          {config.label}
        </span>
      </div>
    </div>
  );
}
