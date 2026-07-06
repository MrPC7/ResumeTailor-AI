"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

type Props = {
  label: string;
  before: number;
  after: number;
  delta: number;
};

function scoreColor(value: number): string {
  if (value >= 80) return "#10b981";
  if (value >= 60) return "#f59e0b";
  if (value >= 40) return "#f97316";
  return "#ef4444";
}

function deltaDisplay(delta: number): { text: string; className: string } {
  if (delta > 0) return { text: `+${delta}`, className: "text-emerald-600" };
  if (delta < 0) return { text: `${delta}`, className: "text-red-600" };
  return { text: "0", className: "text-slate-500" };
}

export function ComparisonMetricCard({ label, before, after, delta }: Props) {
  const [displayedBefore, setDisplayedBefore] = useState(0);
  const [displayedAfter, setDisplayedAfter] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();
    const duration = 800;

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayedBefore(Math.round(before * eased));
      setDisplayedAfter(Math.round(after * eased));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [before, after]);

  const deltaInfo = deltaDisplay(delta);

  return (
    <div
      className="rounded-lg border bg-card p-5 shadow-sm"
      aria-label={`${label}: ${before} before, ${after} after, change ${delta}`}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">{label}</h3>
        <span
          className={cn("text-sm font-bold tabular-nums", deltaInfo.className)}
          aria-label={`Change: ${deltaInfo.text}`}
        >
          {deltaInfo.text}
        </span>
      </div>

      {/* Before / After comparison */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        {/* Before */}
        <div className="text-center">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Before</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-slate-600">{displayedBefore}</p>
          <div
            className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-valuenow={before}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${label} before: ${before}`}
          >
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${Math.max(0, Math.min(100, before))}%`,
                backgroundColor: scoreColor(before),
              }}
            />
          </div>
        </div>

        {/* After */}
        <div className="text-center">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">After</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-emerald-600">{displayedAfter}</p>
          <div
            className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-valuenow={after}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${label} after: ${after}`}
          >
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${Math.max(0, Math.min(100, after))}%`,
                backgroundColor: scoreColor(after),
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
