"use client";

import { cn } from "@/lib/utils";

type Props = {
  gapsBefore: number;
  gapsAfter: number;
  gapsReduced: number;
  strengthsBefore: number;
  strengthsAfter: number;
  strengthsGained: number;
};

export function ComparisonGapReduction({
  gapsBefore,
  gapsAfter,
  gapsReduced,
  strengthsBefore,
  strengthsAfter,
  strengthsGained,
}: Props) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {/* Gaps card */}
      <div
        className="rounded-lg border bg-card p-4 shadow-sm"
        aria-label={`Skill gaps reduced from ${gapsBefore} to ${gapsAfter}`}
      >
        <h3 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <span
            className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-100 text-xs text-red-600"
            aria-hidden="true"
          >
            â†“
          </span>
          Gaps Reduced
        </h3>
        <div className="mt-3 flex items-end gap-4">
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Before</p>
            <p className="text-2xl font-bold tabular-nums text-red-600">{gapsBefore}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">After</p>
            <p className="text-2xl font-bold tabular-nums text-orange-600">{gapsAfter}</p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-xs text-muted-foreground">Reduced</p>
            <p
              className={cn(
                "text-2xl font-bold tabular-nums",
                gapsReduced > 0 ? "text-emerald-600" : "text-slate-500"
              )}
            >
              {gapsReduced > 0 ? `-${gapsReduced}` : gapsReduced}
            </p>
          </div>
        </div>

        {/* Visual bar */}
        <div className="mt-3 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-12 text-xs text-muted-foreground">Before</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-red-400 transition-all duration-500"
                style={{ width: `${gapsBefore > 0 ? Math.min(100, gapsBefore * 20) : 0}%` }}
                role="progressbar"
                aria-valuenow={gapsBefore}
                aria-valuemin={0}
                aria-valuemax={10}
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-12 text-xs text-muted-foreground">After</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-orange-400 transition-all duration-500"
                style={{ width: `${gapsAfter > 0 ? Math.min(100, gapsAfter * 20) : 0}%` }}
                role="progressbar"
                aria-valuenow={gapsAfter}
                aria-valuemin={0}
                aria-valuemax={10}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Strengths card */}
      <div
        className="rounded-lg border bg-card p-4 shadow-sm"
        aria-label={`Strengths increased from ${strengthsBefore} to ${strengthsAfter}`}
      >
        <h3 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <span
            className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-xs text-emerald-600"
            aria-hidden="true"
          >
            â†‘
          </span>
          Strengths Gained
        </h3>
        <div className="mt-3 flex items-end gap-4">
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Before</p>
            <p className="text-2xl font-bold tabular-nums text-slate-600">{strengthsBefore}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">After</p>
            <p className="text-2xl font-bold tabular-nums text-emerald-600">{strengthsAfter}</p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-xs text-muted-foreground">Gained</p>
            <p
              className={cn(
                "text-2xl font-bold tabular-nums",
                strengthsGained > 0 ? "text-emerald-600" : "text-slate-500"
              )}
            >
              {strengthsGained > 0 ? `+${strengthsGained}` : strengthsGained}
            </p>
          </div>
        </div>

        {/* Visual bar */}
        <div className="mt-3 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-12 text-xs text-muted-foreground">Before</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-slate-400 transition-all duration-500"
                style={{
                  width: `${strengthsBefore > 0 ? Math.min(100, strengthsBefore * 20) : 0}%`,
                }}
                role="progressbar"
                aria-valuenow={strengthsBefore}
                aria-valuemin={0}
                aria-valuemax={10}
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-12 text-xs text-muted-foreground">After</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-emerald-400 transition-all duration-500"
                style={{ width: `${strengthsAfter > 0 ? Math.min(100, strengthsAfter * 20) : 0}%` }}
                role="progressbar"
                aria-valuenow={strengthsAfter}
                aria-valuemin={0}
                aria-valuemax={10}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
