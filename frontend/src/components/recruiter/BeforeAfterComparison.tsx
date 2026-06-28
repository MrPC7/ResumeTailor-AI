"use client";

import { cn } from "@/lib/utils";
import type { ReevaluationResult } from "./types";
import { ComparisonMetricCard } from "./ComparisonMetricCard";
import { ComparisonGapReduction } from "./ComparisonGapReduction";
import { ComparisonMatchLevel } from "./ComparisonMatchLevel";
import { ComparisonStrengthsGaps } from "./ComparisonStrengthsGaps";

type Props = {
  result: ReevaluationResult;
  className?: string;
};

export function BeforeAfterComparison({ result, className }: Props) {
  const { before, after, improvement } = result;

  return (
    <section className={cn("space-y-6", className)} aria-label="Before vs After Comparison">
      {/* Improvement summary banner */}
      <div
        className={cn(
          "rounded-lg border p-4 text-center",
          improvement.improved ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-slate-50"
        )}
        role="status"
        aria-live="polite"
      >
        <p
          className={cn(
            "text-sm font-medium",
            improvement.improved ? "text-emerald-700" : "text-slate-700"
          )}
        >
          {improvement.improved
            ? `Resume optimization improved your profile by +${improvement.hiring_confidence_delta} points`
            : "No significant improvement detected â€” consider additional tailoring"}
        </p>
      </div>

      {/* Score comparison cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <ComparisonMetricCard
          label="Hiring Confidence"
          before={before.hiring_confidence}
          after={after.hiring_confidence}
          delta={improvement.hiring_confidence_delta}
        />
        <ComparisonMetricCard
          label="Interview Probability"
          before={before.interview_probability}
          after={after.interview_probability}
          delta={improvement.interview_probability_delta}
        />
      </div>

      {/* Match level transition */}
      <ComparisonMatchLevel
        before={improvement.match_level_before}
        after={improvement.match_level_after}
      />

      {/* Gap reduction */}
      <ComparisonGapReduction
        gapsBefore={improvement.gaps_before}
        gapsAfter={improvement.gaps_after}
        gapsReduced={improvement.gaps_reduced}
        strengthsBefore={improvement.strengths_before}
        strengthsAfter={improvement.strengths_after}
        strengthsGained={improvement.strengths_gained}
      />

      {/* Detailed strengths & gaps lists */}
      <ComparisonStrengthsGaps
        beforeStrengths={before.strengths}
        afterStrengths={after.strengths}
        beforeGaps={before.gaps}
        afterGaps={after.gaps}
      />
    </section>
  );
}
