"use client";

import { cn } from "@/lib/utils";
import type { RecruiterEvaluation } from "./types";
import { RecruiterConfidenceCard } from "./RecruiterConfidenceCard";
import { RecruiterMatchBadge } from "./RecruiterMatchBadge";
import { RecruiterVerdict } from "./RecruiterVerdict";
import { RecruiterStrengths } from "./RecruiterStrengths";
import { RecruiterGaps } from "./RecruiterGaps";

type Props = {
  evaluation: RecruiterEvaluation;
  className?: string;
};

export function RecruiterDashboard({ evaluation, className }: Props) {
  return (
    <section className={cn("space-y-6", className)} aria-label="Recruiter Review Dashboard">
      {/* Top row: confidence scores + match level */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <RecruiterConfidenceCard
          label="Hiring Confidence"
          value={evaluation.hiring_confidence}
          description="How confident a recruiter would be in your candidacy"
        />
        <RecruiterConfidenceCard
          label="Interview Probability"
          value={evaluation.interview_probability}
          description="Likelihood of advancing to an interview"
        />
        <RecruiterMatchBadge matchLevel={evaluation.match_level} />
      </div>

      {/* Verdict */}
      <RecruiterVerdict verdict={evaluation.verdict} />

      {/* Strengths & Gaps */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <RecruiterStrengths strengths={evaluation.strengths} />
        <RecruiterGaps gaps={evaluation.gaps} />
      </div>
    </section>
  );
}
