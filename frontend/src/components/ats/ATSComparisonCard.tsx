"use client";

import { TrendingUp, TrendingDown, Minus, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ATSComparisonResult, ATSScores } from "@/features/workflow/types/workflow.types";

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

type DimensionRowProps = {
  label: string;
  before: number;
  after: number;
};

function DimensionRow({ label, before, after }: DimensionRowProps) {
  const delta = after - before;
  const barColor = (v: number) =>
    v >= 80 ? "bg-emerald-500" : v >= 60 ? "bg-amber-500" : "bg-red-500";
  const deltaColor = delta > 0 ? "text-emerald-600" : delta < 0 ? "text-red-600" : "text-slate-400";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-slate-700">{label}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs tabular-nums text-slate-500">{before}</span>
          <ArrowRight className="h-3 w-3 text-slate-300" />
          <span className="text-xs font-semibold tabular-nums text-slate-700">{after}</span>
          <span
            className={cn("min-w-[36px] text-right text-xs font-bold tabular-nums", deltaColor)}
          >
            {delta > 0 ? "+" : ""}
            {delta}
          </span>
        </div>
      </div>
      <div className="flex h-2 gap-1">
        <div className="flex-1 overflow-hidden rounded-full bg-slate-100">
          <div
            className={cn("h-full rounded-full transition-all duration-500", barColor(before))}
            style={{ width: `${before}%`, opacity: 0.4 }}
          />
        </div>
        <div className="flex-1 overflow-hidden rounded-full bg-slate-100">
          <div
            className={cn("h-full rounded-full transition-all duration-700", barColor(after))}
            style={{ width: `${after}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export function ATSComparisonCard({ comparison }: Props) {
  const { beforeScore, afterScore, improvement, before, after } = comparison;
  const isPositive = improvement > 0;
  const isNeutral = improvement === 0;

  const dimensions: { label: string; key: keyof ATSScores }[] = [
    { label: "Skills Match", key: "skills" },
    { label: "Keyword Coverage", key: "keywords" },
    { label: "Experience Fit", key: "experience" },
    { label: "Education", key: "education" },
    { label: "Overall Fit", key: "overallFit" },
  ];

  return (
    <div className="space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      {/* Header */}
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

      {/* Overall score pills */}
      <div className="flex items-center justify-center gap-4">
        <ScorePill score={beforeScore} label="Before" />

        <div className="flex flex-col items-center text-slate-400">
          <div className="h-0.5 w-8 bg-slate-200" />
          <span className="mt-1 text-xs">→</span>
        </div>

        <ScorePill score={afterScore} label="After" />
      </div>

      {isPositive && (
        <p className="text-center text-xs font-medium text-emerald-600">
          Resume optimized — ATS score improved by {improvement} point{improvement !== 1 ? "s" : ""}
          !
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

      {/* Per-dimension breakdown */}
      <div className="space-y-1 pt-1">
        <div className="mb-2 flex items-center justify-between">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Dimension Breakdown
          </h4>
          <div className="flex items-center gap-3 text-[10px] text-slate-400">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-4 rounded-full bg-slate-300 opacity-40" />
              Before
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-4 rounded-full bg-emerald-500" />
              After
            </span>
          </div>
        </div>
        {dimensions.map((dim) => (
          <DimensionRow
            key={dim.key}
            label={dim.label}
            before={before.scores[dim.key]}
            after={after.scores[dim.key]}
          />
        ))}
      </div>
    </div>
  );
}
