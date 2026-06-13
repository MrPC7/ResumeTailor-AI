"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ATSComparisonResult } from "@/features/workflow/types/workflow.types";

type Props = {
  comparison: ATSComparisonResult;
};

function ScorePill({ score, label }: { score: number; label: string }) {
  const color =
    score >= 80
      ? "border-emerald-300 bg-emerald-50 text-emerald-700"
      : score >= 60
        ? "border-amber-300 bg-amber-50 text-amber-700"
        : "border-red-300 bg-red-50 text-red-700";

  return (
    <div className={cn("flex flex-col items-center rounded-xl border-2 px-6 py-4", color)}>
      <span className="text-4xl font-extrabold tabular-nums leading-none">{score}</span>
      <span className="mt-1 text-xs font-medium opacity-80">{label}</span>
    </div>
  );
}

export function ATSComparisonCard({ comparison }: Props) {
  const { beforeScore, afterScore, improvement } = comparison;
  const isPositive = improvement > 0;
  const isNeutral = improvement === 0;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Before vs After Optimization</h3>
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold",
            isPositive && "bg-emerald-100 text-emerald-700",
            isNeutral && "bg-slate-100 text-slate-600",
            !isPositive && !isNeutral && "bg-red-100 text-red-700"
          )}
        >
          {isPositive ? (
            <TrendingUp className="h-3.5 w-3.5" />
          ) : isNeutral ? (
            <Minus className="h-3.5 w-3.5" />
          ) : (
            <TrendingDown className="h-3.5 w-3.5" />
          )}
          {isPositive ? "+" : ""}
          {improvement} pts
        </span>
      </div>

      <div className="flex items-center justify-center gap-4">
        <ScorePill score={beforeScore} label="Before" />

        <div className="flex flex-col items-center text-slate-400">
          <div className="h-0.5 w-8 bg-slate-200" />
          <span className="mt-1 text-xs">→</span>
        </div>

        <ScorePill score={afterScore} label="After" />
      </div>

      {isPositive && (
        <p className="text-center text-xs text-emerald-600 font-medium">
          Resume optimized — ATS score improved by {improvement} point{improvement !== 1 ? "s" : ""}!
        </p>
      )}
      {isNeutral && (
        <p className="text-center text-xs text-slate-500">
          Score unchanged — resume was already well-optimized.
        </p>
      )}
      {!isPositive && !isNeutral && (
        <p className="text-center text-xs text-red-600">
          Score decreased by {Math.abs(improvement)} point{Math.abs(improvement) !== 1 ? "s" : ""}.
        </p>
      )}
    </div>
  );
}
