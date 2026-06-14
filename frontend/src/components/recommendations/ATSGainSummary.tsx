"use client";

import { ArrowRight, TrendingUp, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  currentScore: number;
  potentialScore: number;
  selectedGain: number;
};

function scoreColor(value: number): string {
  if (value >= 80) return "text-emerald-600";
  if (value >= 60) return "text-amber-600";
  return "text-red-500";
}

function progressColor(value: number): string {
  if (value >= 80) return "bg-emerald-500";
  if (value >= 60) return "bg-amber-500";
  return "bg-red-500";
}

export function ATSGainSummary({ currentScore, potentialScore, selectedGain }: Props) {
  const projectedScore = Math.min(currentScore + selectedGain, potentialScore);

  return (
    <div className="grid grid-cols-3 gap-3">
      {/* Current Score */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400 mb-1">
          Current
        </p>
        <p className={cn("text-3xl font-extrabold tabular-nums", scoreColor(currentScore))}>
          {currentScore}
        </p>
        <div className="mt-2 h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-300", progressColor(currentScore))}
            style={{ width: `${currentScore}%` }}
          />
        </div>
      </div>

      {/* Projected (selected gain) */}
      <div className="rounded-xl border-2 border-blue-200 bg-gradient-to-b from-blue-50 to-white p-4 text-center relative">
        <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 flex items-center gap-1 rounded-full bg-blue-600 px-2.5 py-0.5">
          <Zap className="h-3 w-3 text-white" />
          <span className="text-[10px] font-bold text-white">
            +{selectedGain} pts
          </span>
        </div>
        <p className="text-[11px] font-medium uppercase tracking-wide text-blue-500 mb-1 mt-1">
          Projected
        </p>
        <p className={cn("text-3xl font-extrabold tabular-nums", scoreColor(projectedScore))}>
          {projectedScore}
        </p>
        <div className="mt-2 h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", progressColor(projectedScore))}
            style={{ width: `${projectedScore}%` }}
          />
        </div>
      </div>

      {/* Potential (ceiling) */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400 mb-1">
          Potential
        </p>
        <p className={cn("text-3xl font-extrabold tabular-nums", scoreColor(potentialScore))}>
          {potentialScore}
        </p>
        <div className="mt-2 h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-300", progressColor(potentialScore))}
            style={{ width: `${potentialScore}%` }}
          />
        </div>
      </div>
    </div>
  );
}
