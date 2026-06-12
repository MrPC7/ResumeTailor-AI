"use client";

import { cn } from "@/lib/utils";
import { DiffSection, InlineDiff } from "@/features/resume-diff/components/DiffSection";
import type { ResumeDiff } from "@/features/resume-diff/types/diff.types";

type Props = {
  diff: ResumeDiff;
};

const BADGE: Record<string, string> = {
  added: "bg-emerald-100 text-emerald-800",
  removed: "bg-red-100 text-red-800",
  unchanged: "bg-slate-100 text-slate-600",
};

function Legend() {
  return (
    <div className="flex items-center gap-4 text-xs text-slate-600">
      <span className="flex items-center gap-1">
        <span className="inline-block h-3 w-3 rounded bg-emerald-100" />
        Added
      </span>
      <span className="flex items-center gap-1">
        <span className="inline-block h-3 w-3 rounded bg-red-100" />
        Removed
      </span>
    </div>
  );
}

export function ResumeDiffViewer({ diff }: Props) {
  const hasSkillChanges = diff.skillsDiff.some((s) => s.status !== "unchanged");
  const hasSummaryChanges = diff.summaryDiff.some((t) => t.status !== "unchanged");

  return (
    <div className="space-y-6">
      {/* Legend */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900">Resume Changes</h2>
        <Legend />
      </div>

      {/* Identity fields — only show if changed */}
      {diff.nameDiff.some((t) => t.status !== "unchanged") && (
        <DiffSection title="Name">
          <InlineDiff tokens={diff.nameDiff} />
        </DiffSection>
      )}
      {diff.emailDiff.some((t) => t.status !== "unchanged") && (
        <DiffSection title="Email">
          <InlineDiff tokens={diff.emailDiff} />
        </DiffSection>
      )}
      {diff.phoneDiff.some((t) => t.status !== "unchanged") && (
        <DiffSection title="Phone">
          <InlineDiff tokens={diff.phoneDiff} />
        </DiffSection>
      )}

      {/* Summary */}
      {hasSummaryChanges && (
        <DiffSection title="Summary">
          <InlineDiff tokens={diff.summaryDiff} />
        </DiffSection>
      )}

      {/* Skills */}
      {hasSkillChanges && (
        <DiffSection title="Skills">
          <div className="flex flex-wrap gap-2">
            {diff.skillsDiff.map((item, index) => (
              <span
                key={index}
                className={cn(
                  "rounded-full px-2.5 py-0.5 text-xs font-medium",
                  BADGE[item.status],
                  item.status === "removed" && "line-through"
                )}
              >
                {item.value}
              </span>
            ))}
          </div>
        </DiffSection>
      )}

      {/* Experience */}
      {diff.experienceDiff.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Experience
          </h3>
          {diff.experienceDiff.map((exp, index) => {
            const changed = exp.descriptionDiff.some((t) => t.status !== "unchanged");
            if (!changed) return null;
            return (
              <div key={index} className="rounded-md border border-slate-200 bg-white p-3">
                <p className="mb-1.5 text-sm font-medium text-slate-900">
                  {exp.position}{" "}
                  <span className="font-normal text-slate-500">at {exp.company}</span>
                </p>
                <p className="text-sm leading-relaxed">
                  <InlineDiff tokens={exp.descriptionDiff} />
                </p>
              </div>
            );
          })}
        </div>
      )}

      {/* Projects */}
      {diff.projectsDiff.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Projects
          </h3>
          {diff.projectsDiff.map((proj, index) => {
            const changed = proj.descriptionDiff.some((t) => t.status !== "unchanged");
            if (!changed) return null;
            return (
              <div key={index} className="rounded-md border border-slate-200 bg-white p-3">
                <p className="mb-1.5 text-sm font-medium text-slate-900">{proj.name}</p>
                <p className="text-sm leading-relaxed">
                  <InlineDiff tokens={proj.descriptionDiff} />
                </p>
              </div>
            );
          })}
        </div>
      )}

      {/* No changes indicator */}
      {!hasSummaryChanges &&
        !hasSkillChanges &&
        diff.experienceDiff.every((e) =>
          e.descriptionDiff.every((t) => t.status === "unchanged")
        ) &&
        diff.projectsDiff.every((p) =>
          p.descriptionDiff.every((t) => t.status === "unchanged")
        ) && <p className="text-sm text-slate-500">No changes detected between the two resumes.</p>}
    </div>
  );
}
