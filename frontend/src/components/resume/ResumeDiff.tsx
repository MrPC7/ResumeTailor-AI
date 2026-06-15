"use client";

import { CheckCircle2, Minus, Plus } from "lucide-react";
import type {
  StructuredResume,
  ExperienceItem,
  ProjectItem,
} from "@/features/workflow/types/workflow.types";

// ── Helpers ──────────────────────────────────────────────────────────────

function skillKey(s: string) {
  return s.toLowerCase().trim();
}

function isDifferent(a: string | null | undefined, b: string | null | undefined): boolean {
  return (a ?? "").trim() !== (b ?? "").trim();
}

// Find experience items that changed, keyed by company+position
function diffExperience(
  before: ExperienceItem[],
  after: ExperienceItem[],
): Array<{ before: ExperienceItem; after: ExperienceItem }> {
  const changes: Array<{ before: ExperienceItem; after: ExperienceItem }> = [];
  for (const afterItem of after) {
    const beforeItem = before.find(
      (b) =>
        b.company?.toLowerCase() === afterItem.company?.toLowerCase() &&
        b.position?.toLowerCase() === afterItem.position?.toLowerCase(),
    );
    if (beforeItem && isDifferent(beforeItem.description, afterItem.description)) {
      changes.push({ before: beforeItem, after: afterItem });
    }
  }
  return changes;
}

// Find project items that changed, keyed by name
function diffProjects(
  before: ProjectItem[],
  after: ProjectItem[],
): Array<{ before: ProjectItem; after: ProjectItem }> {
  const changes: Array<{ before: ProjectItem; after: ProjectItem }> = [];
  for (const afterItem of after) {
    const beforeItem = before.find(
      (b) => b.name?.toLowerCase() === afterItem.name?.toLowerCase(),
    );
    if (beforeItem && isDifferent(beforeItem.description, afterItem.description)) {
      changes.push({ before: beforeItem, after: afterItem });
    }
  }
  return changes;
}

// ── Sub-components ────────────────────────────────────────────────────────

function DiffSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <div className="border-b border-slate-100 bg-slate-50 px-5 py-3">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

function BeforeAfterBlock({
  label,
  before,
  after,
}: {
  label?: string;
  before: string;
  after: string;
}) {
  return (
    <div className="space-y-2">
      {label && (
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-red-100 bg-red-50 p-3">
          <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-red-400">
            Before
          </p>
          <p className="text-sm leading-relaxed text-slate-600 whitespace-pre-line">{before}</p>
        </div>
        <div className="rounded-lg border border-emerald-100 bg-emerald-50 p-3">
          <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-emerald-500">
            After
          </p>
          <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-line">{after}</p>
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────

type Props = {
  original: StructuredResume;
  customized: StructuredResume;
};

export function ResumeDiff({ original, customized }: Props) {
  const originalSkillSet = new Set(original.skills.map(skillKey));
  const customizedSkillSet = new Set(customized.skills.map(skillKey));

  const addedSkills = customized.skills.filter((s) => !originalSkillSet.has(skillKey(s)));
  const removedSkills = original.skills.filter((s) => !customizedSkillSet.has(skillKey(s)));
  const skillsChanged = addedSkills.length > 0 || removedSkills.length > 0;

  const summaryChanged = isDifferent(original.summary, customized.summary);
  const experienceChanges = diffExperience(original.experience, customized.experience);
  const projectChanges = diffProjects(original.projects, customized.projects);

  const totalChanges =
    (skillsChanged ? 1 : 0) +
    (summaryChanged ? 1 : 0) +
    experienceChanges.length +
    projectChanges.length;

  if (totalChanges === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-slate-200 bg-white py-16 text-center">
        <CheckCircle2 className="h-10 w-10 text-emerald-500" />
        <p className="mt-3 font-semibold text-slate-800">No changes detected</p>
        <p className="mt-1 text-sm text-slate-400">
          The optimized resume is identical to the original.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Change count banner */}
      <div className="flex items-center gap-2 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
          {totalChanges}
        </span>
        <p className="text-sm font-medium text-blue-800">
          {totalChanges} section{totalChanges !== 1 ? "s" : ""} improved
        </p>
      </div>

      {/* ── Skills ──────────────────────────────────────────────── */}
      {skillsChanged && (
        <DiffSection title="Skills">
          <div className="space-y-3">
            {addedSkills.length > 0 && (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-emerald-600">
                  <Plus className="h-3.5 w-3.5" />
                  Added ({addedSkills.length})
                </p>
                <div className="flex flex-wrap gap-2">
                  {addedSkills.map((s) => (
                    <span
                      key={s}
                      className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700"
                    >
                      <Plus className="h-3 w-3" />
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {removedSkills.length > 0 && (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-red-500">
                  <Minus className="h-3.5 w-3.5" />
                  Removed ({removedSkills.length})
                </p>
                <div className="flex flex-wrap gap-2">
                  {removedSkills.map((s) => (
                    <span
                      key={s}
                      className="inline-flex items-center gap-1 rounded-md border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-medium text-red-600 line-through"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </DiffSection>
      )}

      {/* ── Summary ─────────────────────────────────────────────── */}
      {summaryChanged && (
        <DiffSection title="Summary">
          <BeforeAfterBlock
            before={original.summary ?? ""}
            after={customized.summary ?? ""}
          />
        </DiffSection>
      )}

      {/* ── Experience ──────────────────────────────────────────── */}
      {experienceChanges.length > 0 && (
        <DiffSection title="Experience">
          <div className="space-y-5">
            {experienceChanges.map(({ before, after }, i) => (
              <div key={i}>
                <p className="mb-2 text-sm font-semibold text-slate-800">
                  {after.position}
                  {after.company ? (
                    <span className="font-normal text-slate-500"> · {after.company}</span>
                  ) : null}
                </p>
                <BeforeAfterBlock
                  before={before.description}
                  after={after.description}
                />
                {i < experienceChanges.length - 1 && (
                  <div className="mt-5 border-b border-slate-100" />
                )}
              </div>
            ))}
          </div>
        </DiffSection>
      )}

      {/* ── Projects ────────────────────────────────────────────── */}
      {projectChanges.length > 0 && (
        <DiffSection title="Projects">
          <div className="space-y-5">
            {projectChanges.map(({ before, after }, i) => (
              <div key={i}>
                <p className="mb-2 text-sm font-semibold text-slate-800">{after.name}</p>
                <BeforeAfterBlock
                  before={before.description}
                  after={after.description}
                />
                {i < projectChanges.length - 1 && (
                  <div className="mt-5 border-b border-slate-100" />
                )}
              </div>
            ))}
          </div>
        </DiffSection>
      )}
    </div>
  );
}
