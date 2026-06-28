"use client";

import { cn } from "@/lib/utils";

type Props = {
  beforeStrengths: string[];
  afterStrengths: string[];
  beforeGaps: string[];
  afterGaps: string[];
};

function ListItem({
  text,
  variant,
  removed,
  added,
}: {
  text: string;
  variant: "strength" | "gap";
  removed?: boolean;
  added?: boolean;
}) {
  const dotColor = variant === "strength" ? "bg-emerald-500" : "bg-red-500";

  return (
    <li
      className={cn(
        "flex items-start gap-2 text-sm",
        removed && "text-muted-foreground line-through opacity-60",
        added && "font-medium",
        !removed && !added && "text-foreground"
      )}
    >
      <span
        className={cn("mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full", dotColor)}
        aria-hidden="true"
      />
      <span className="flex-1">{text}</span>
      {added && (
        <span className="shrink-0 rounded-full bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700">
          NEW
        </span>
      )}
      {removed && (
        <span className="shrink-0 rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-semibold text-red-700">
          RESOLVED
        </span>
      )}
    </li>
  );
}

export function ComparisonStrengthsGaps({
  beforeStrengths,
  afterStrengths,
  beforeGaps,
  afterGaps,
}: Props) {
  const newStrengths = afterStrengths.filter((s) => !beforeStrengths.includes(s));
  const keptStrengths = afterStrengths.filter((s) => beforeStrengths.includes(s));

  const resolvedGaps = beforeGaps.filter((g) => !afterGaps.includes(g));
  const remainingGaps = afterGaps.filter((g) => beforeGaps.includes(g));
  const newGaps = afterGaps.filter((g) => !beforeGaps.includes(g));

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {/* Strengths comparison */}
      <div
        className="rounded-lg border bg-card p-4 shadow-sm"
        aria-label={`Strengths: ${beforeStrengths.length} before, ${afterStrengths.length} after`}
      >
        <h3 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <span
            className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"
            aria-hidden="true"
          >
            ✓
          </span>
          Strengths
          <span className="ml-auto flex items-center gap-1">
            <span className="text-xs tabular-nums text-slate-500">{beforeStrengths.length}</span>
            <span className="text-xs text-slate-400" aria-hidden="true">
              →
            </span>
            <span className="text-xs font-semibold tabular-nums text-emerald-600">
              {afterStrengths.length}
            </span>
          </span>
        </h3>
        <ul className="mt-3 space-y-2" role="list" aria-label="Strengths after optimization">
          {keptStrengths.map((s, i) => (
            <ListItem key={`kept-${i}`} text={s} variant="strength" />
          ))}
          {newStrengths.map((s, i) => (
            <ListItem key={`new-${i}`} text={s} variant="strength" added />
          ))}
        </ul>
        {afterStrengths.length === 0 && (
          <p className="mt-3 text-xs text-muted-foreground">No strengths identified</p>
        )}
      </div>

      {/* Gaps comparison */}
      <div
        className="rounded-lg border bg-card p-4 shadow-sm"
        aria-label={`Skill gaps: ${beforeGaps.length} before, ${afterGaps.length} after`}
      >
        <h3 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <span
            className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-100 text-red-600"
            aria-hidden="true"
          >
            !
          </span>
          Skill Gaps
          <span className="ml-auto flex items-center gap-1">
            <span className="text-xs tabular-nums text-slate-500">{beforeGaps.length}</span>
            <span className="text-xs text-slate-400" aria-hidden="true">
              →
            </span>
            <span
              className={cn(
                "text-xs font-semibold tabular-nums",
                afterGaps.length < beforeGaps.length ? "text-emerald-600" : "text-red-600"
              )}
            >
              {afterGaps.length}
            </span>
          </span>
        </h3>
        <ul className="mt-3 space-y-2" role="list" aria-label="Skill gaps after optimization">
          {resolvedGaps.map((g, i) => (
            <ListItem key={`resolved-${i}`} text={g} variant="gap" removed />
          ))}
          {remainingGaps.map((g, i) => (
            <ListItem key={`remaining-${i}`} text={g} variant="gap" />
          ))}
          {newGaps.map((g, i) => (
            <ListItem key={`new-${i}`} text={g} variant="gap" added />
          ))}
        </ul>
        {afterGaps.length === 0 && resolvedGaps.length === 0 && (
          <p className="mt-3 text-xs text-muted-foreground">No gaps identified</p>
        )}
        {afterGaps.length === 0 && resolvedGaps.length > 0 && (
          <p className="mt-3 text-xs font-medium text-emerald-600">
            All gaps resolved!
          </p>
        )}
      </div>
    </div>
  );
}
