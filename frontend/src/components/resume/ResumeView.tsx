"use client";

import type {
  StructuredResume,
  ExperienceItem,
  EducationItem,
  ProjectItem,
} from "@/features/workflow/types/workflow.types";

type Props = {
  resume: StructuredResume;
};

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-center gap-3">
      <h2 className="text-[11px] font-bold uppercase tracking-[0.12em] text-slate-400">
        {children}
      </h2>
      <div className="h-px flex-1 bg-slate-200" />
    </div>
  );
}

function ExperienceEntry({ item }: { item: ExperienceItem }) {
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:justify-between">
        <div>
          <span className="font-semibold text-slate-900">{item.position}</span>
          {item.company && <span className="text-slate-600"> · {item.company}</span>}
        </div>
        {item.duration && <span className="shrink-0 text-xs text-slate-400">{item.duration}</span>}
      </div>
      {item.description && (
        <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-slate-600">
          {item.description}
        </p>
      )}
    </div>
  );
}

function EducationEntry({ item }: { item: EducationItem }) {
  return (
    <div className="mb-3 last:mb-0">
      <div className="flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:justify-between">
        <div>
          <span className="font-semibold text-slate-900">{item.degree}</span>
          {item.institution && <span className="text-slate-600"> · {item.institution}</span>}
        </div>
        {item.year && <span className="shrink-0 text-xs text-slate-400">{item.year}</span>}
      </div>
    </div>
  );
}

function ProjectEntry({ item }: { item: ProjectItem }) {
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <span className="font-semibold text-slate-900">{item.name}</span>
        {item.technologies.length > 0 && (
          <span className="text-xs text-slate-400">{item.technologies.join(" · ")}</span>
        )}
      </div>
      {item.description && (
        <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-slate-600">
          {item.description}
        </p>
      )}
    </div>
  );
}

export function ResumeView({ resume }: Props) {
  return (
    <article className="mx-auto max-w-3xl space-y-6 rounded-xl border border-slate-200 bg-white px-8 py-8 shadow-sm">
      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="space-y-1 text-center">
        {resume.name && (
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{resume.name}</h1>
        )}
        {(resume.email || resume.phone) && (
          <p className="text-sm text-slate-500">
            {[resume.email, resume.phone].filter(Boolean).join(" · ")}
          </p>
        )}
      </header>

      {/* ── Summary ─────────────────────────────────────────────── */}
      {resume.summary && (
        <section>
          <SectionHeading>Summary</SectionHeading>
          <p className="text-sm leading-relaxed text-slate-700">{resume.summary}</p>
        </section>
      )}

      {/* ── Skills ──────────────────────────────────────────────── */}
      {resume.skills.length > 0 && (
        <section>
          <SectionHeading>Skills</SectionHeading>
          <div className="flex flex-wrap gap-2">
            {resume.skills.map((skill) => (
              <span
                key={skill}
                className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700"
              >
                {skill}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* ── Experience ──────────────────────────────────────────── */}
      {resume.experience.length > 0 && (
        <section>
          <SectionHeading>Experience</SectionHeading>
          {resume.experience.map((item, i) => (
            <ExperienceEntry key={i} item={item} />
          ))}
        </section>
      )}

      {/* ── Education ───────────────────────────────────────────── */}
      {resume.education.length > 0 && (
        <section>
          <SectionHeading>Education</SectionHeading>
          {resume.education.map((item, i) => (
            <EducationEntry key={i} item={item} />
          ))}
        </section>
      )}

      {/* ── Projects ────────────────────────────────────────────── */}
      {resume.projects.length > 0 && (
        <section>
          <SectionHeading>Projects</SectionHeading>
          {resume.projects.map((item, i) => (
            <ProjectEntry key={i} item={item} />
          ))}
        </section>
      )}
    </article>
  );
}
