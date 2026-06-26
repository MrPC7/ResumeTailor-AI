"use client";

import { cn } from "@/lib/utils";

type Props = {
  gaps: string[];
};

export function RecruiterGaps({ gaps }: Props) {
  if (gaps.length === 0) return null;

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <h3 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <span
          className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-100 text-red-600"
          aria-hidden="true"
        >
          !
        </span>
        Skill Gaps
        <span className="ml-auto text-xs text-red-600 font-semibold">
          {gaps.length}
        </span>
      </h3>
      <ul className="mt-3 space-y-2" role="list" aria-label="Skill gaps identified by recruiter">
        {gaps.map((gap, idx) => (
          <li
            key={idx}
            className="flex items-start gap-2 text-sm text-foreground"
          >
            <span
              className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-red-500"
              aria-hidden="true"
            />
            {gap}
          </li>
        ))}
      </ul>
    </div>
  );
}
