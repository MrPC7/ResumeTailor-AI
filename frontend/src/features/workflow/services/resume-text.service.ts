import type { StructuredResume } from "@/features/workflow/types/workflow.types";

export function resumeToText(resume: StructuredResume): string {
  const lines: string[] = [];

  if (resume.name) lines.push(resume.name);
  if (resume.email || resume.phone) {
    lines.push([resume.email, resume.phone].filter(Boolean).join(" | "));
  }
  if (resume.summary) {
    lines.push("", "Summary", resume.summary);
  }
  if (resume.skills.length > 0) {
    lines.push("", "Skills", resume.skills.join(", "));
  }
  if (resume.experience.length > 0) {
    lines.push("", "Experience");
    resume.experience.forEach((item) => {
      lines.push(`${item.position} - ${item.company}`);
      if (item.duration) lines.push(item.duration);
      if (item.description) lines.push(item.description);
    });
  }
  if (resume.projects.length > 0) {
    lines.push("", "Projects");
    resume.projects.forEach((project) => {
      lines.push(project.name);
      if (project.description) lines.push(project.description);
      if (project.technologies.length > 0) {
        lines.push(`Technologies: ${project.technologies.join(", ")}`);
      }
    });
  }
  if (resume.education.length > 0) {
    lines.push("", "Education");
    resume.education.forEach((item) => {
      lines.push([item.degree, item.institution, item.year].filter(Boolean).join(" - "));
    });
  }

  return lines.join("\n").trim();
}
