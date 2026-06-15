"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

type Props = {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  animate?: boolean;
};

function scoreColor(score: number): string {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#f59e0b";
  return "#ef4444";
}

function scoreTextColor(score: number): string {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-red-600";
}

function scoreLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  return "Needs Work";
}

export function ATSScoreCard({
  score,
  size = 160,
  strokeWidth = 12,
  label,
  animate = true,
}: Props) {
  const [displayed, setDisplayed] = useState(animate ? 0 : score);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!animate) {
      setDisplayed(score);
      return;
    }
    const start = performance.now();
    const duration = 900;
    const from = 0;
    const to = score;

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(Math.round(from + (to - from) * eased));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [score, animate]);

  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const center = size / 2;
  const color = scoreColor(score);

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className="relative flex items-center justify-center"
        style={{ width: size, height: size }}
      >
        <svg
          className="-rotate-90"
          width={size}
          height={size}
          aria-label={`ATS score ${score} out of 100`}
          role="img"
        >
          {/* Track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.16,1,0.3,1)" }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span
            className={cn("font-bold tabular-nums leading-none", scoreTextColor(score))}
            style={{ fontSize: size * 0.22 }}
          >
            {displayed}
          </span>
          <span className="text-xs text-slate-400">/ 100</span>
        </div>
      </div>
      <div className="text-center">
        <p className={cn("text-sm font-semibold", scoreTextColor(score))}>{scoreLabel(score)}</p>
        {label && <p className="text-xs text-slate-500">{label}</p>}
      </div>
    </div>
  );
}
