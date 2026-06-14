"use client";

import { cn } from "@/lib/utils";
import type { ImpactLevel } from "@/features/workflow/types/workflow.types";

const STYLES: Record<ImpactLevel, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  low: "bg-slate-100 text-slate-600 border-slate-200",
};

type Props = {
  level: ImpactLevel;
  className?: string;
};

export function ImpactBadge({ level, className }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase leading-none",
        STYLES[level],
        className,
      )}
    >
      {level}
    </span>
  );
}
