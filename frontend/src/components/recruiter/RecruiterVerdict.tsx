"use client";

type Props = {
  verdict: string;
};

export function RecruiterVerdict({ verdict }: Props) {
  if (!verdict) return null;

  return (
    <div
      className="rounded-lg border bg-card p-4 shadow-sm"
      aria-label="Recruiter Verdict"
    >
      <h3 className="text-sm font-medium text-muted-foreground">
        Recruiter Verdict
      </h3>
      <p className="mt-2 text-base font-medium text-foreground leading-relaxed">
        &ldquo;{verdict}&rdquo;
      </p>
    </div>
  );
}
