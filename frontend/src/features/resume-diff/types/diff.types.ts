export type DiffStatus = "added" | "removed" | "unchanged";

export type DiffToken = {
  text: string;
  status: DiffStatus;
};

export type DiffItem = {
  value: string;
  status: DiffStatus;
};

export type ExperienceDiff = {
  company: string;
  position: string;
  duration: string;
  descriptionDiff: DiffToken[];
};

export type ProjectDiff = {
  name: string;
  descriptionDiff: DiffToken[];
  technologies: string[];
};

export type ResumeDiff = {
  nameDiff: DiffToken[];
  emailDiff: DiffToken[];
  phoneDiff: DiffToken[];
  summaryDiff: DiffToken[];
  skillsDiff: DiffItem[];
  experienceDiff: ExperienceDiff[];
  projectsDiff: ProjectDiff[];
};

export type ResumeDiffResponse = {
  diff: ResumeDiff;
};
