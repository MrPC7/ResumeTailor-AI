"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

type Props = {
  label: string;
  value: number;
  description?: string;
};

function confidenceColor(value: number): string {
  if (value >= 80) return "#10b981";
  if (value >= 60) return "#f59e0b";
  if (value >= 40) return "#f97316";
  return "#ef4444";
}

function confidenceTextColor(value: number): string {
  if (value >= 80) return "text-emerald-600";
  if (value >= 60) return "text-amber-600";
  if (value >= 40) return "text-orange-600";
  return "text-red-600";
}

function confidenceLabel(value: number): string {
  if (value >= 80) return "Strong";
  if (value >= 60) return "Good";
  if (value >= 40) return "Moderate";
  if (value >= 20) return "Low";
  return "Very Low";
}

export function RecruiterConfidenceCard({ label, value, description }: Props) {
  const [displayed, setDisplayed] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();
    const duration = 800;

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(Math.round(value * eased));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [value]);

  const color = confidenceColor(value);
  const barWidth = `${Math.max(0, Math.min(100, value))}%`;

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">{label}</h3>
        <span className={cn("text-xs font-semibold", confidenceTextColor(value))}>
          {confidenceLabel(value)}
        </span>
      </div>

      <p
        className={cn(
          "mt-2 text-3xl font-bold tabular-nums",
          confidenceTextColor(value)
        )}
        aria-label={`${label}: ${value} out of 100`}
      >
        {displayed}
        <span className="text-lg text-muted-foreground">/100</span>
      </p>

      {/* Progress bar */}
      <div
        className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: barWidth, backgroundColor: color }}
        />
      </div>

      {description && (
        <p className="mt-2 text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
