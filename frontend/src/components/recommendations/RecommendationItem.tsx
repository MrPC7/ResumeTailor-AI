"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { ImpactBadge } from "@/components/recommendations/ImpactBadge";
import type { Recommendation } from "@/features/workflow/types/workflow.types";

type Props = {
  recommendation: Recommendation;
  checked: boolean;
  onToggle: (id: string) => void;
  highlighted?: boolean;
};

export function RecommendationItem({
  recommendation,
  checked,
  onToggle,
  highlighted = false,
}: Props) {
  const { id, title, description, impactLevel, estimatedPoints } = recommendation;

  return (
    <div
      className={cn(
        "flex cursor-pointer items-start gap-3 rounded-lg border px-3.5 py-2.5 transition-all duration-150",
        checked
          ? "border-emerald-200 bg-emerald-50/80 shadow-sm"
          : "border-slate-200 bg-white opacity-60 hover:opacity-80",
        highlighted && "ring-2 ring-blue-300 ring-offset-1"
      )}
      onClick={() => onToggle(id)}
      role="checkbox"
      aria-checked={checked}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === " " || e.key === "Enter") {
          e.preventDefault();
          onToggle(id);
        }
      }}
    >
      {/* Checkbox */}
      <button
        type="button"
        className={cn(
          "mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded border-2 transition-colors",
          checked ? "border-emerald-600 bg-emerald-600 text-white" : "border-slate-300 bg-white"
        )}
        aria-label={checked ? `Deselect: ${title}` : `Select: ${title}`}
        tabIndex={-1}
      >
        {checked && <Check className="h-3 w-3" />}
      </button>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium leading-tight text-slate-800">{title}</span>
          <ImpactBadge level={impactLevel} />
          <span className="text-[11px] font-semibold tabular-nums text-blue-600">
            +{estimatedPoints} pts
          </span>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">{description}</p>
      </div>
    </div>
  );
}
