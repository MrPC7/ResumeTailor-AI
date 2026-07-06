"use client";

type Props = {
  strengths: string[];
};

export function RecruiterStrengths({ strengths }: Props) {
  if (strengths.length === 0) return null;

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <h3 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <span
          className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"
          aria-hidden="true"
        >
          âœ“
        </span>
        Strengths
        <span className="ml-auto text-xs font-semibold text-emerald-600">{strengths.length}</span>
      </h3>
      <ul className="mt-3 space-y-2" role="list" aria-label="Candidate strengths">
        {strengths.map((strength, idx) => (
          <li key={idx} className="flex items-start gap-2 text-sm text-foreground">
            <span
              className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500"
              aria-hidden="true"
            />
            {strength}
          </li>
        ))}
      </ul>
    </div>
  );
}
