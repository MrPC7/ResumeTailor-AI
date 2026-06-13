"use client";

import { CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  keywords: string[];
};

const CHIP_COLORS = [
  "bg-emerald-50 text-emerald-700 border-emerald-200",
  "bg-blue-50 text-blue-700 border-blue-200",
  "bg-violet-50 text-violet-700 border-violet-200",
  "bg-teal-50 text-teal-700 border-teal-200",
];

export function KeywordHeatmap({ keywords }: Props) {
  if (keywords.length === 0) {
    return (
      <p className="text-sm text-slate-400 italic">No matched keywords found.</p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {keywords.map((kw, i) => (
        <span
          key={kw}
          className={cn(
            "inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium",
            CHIP_COLORS[i % CHIP_COLORS.length]
          )}
        >
          <CheckCircle2 className="h-3 w-3 shrink-0" />
          {kw}
        </span>
      ))}
    </div>
  );
}
