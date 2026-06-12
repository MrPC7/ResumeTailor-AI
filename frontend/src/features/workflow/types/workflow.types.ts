import type { ResumeDiff } from "@/features/resume-diff/types/diff.types";

export type WorkflowStep = "upload" | "jd" | "analyze" | "preview" | "download";

export type ExperienceItem = {
  company: string;
  position: string;
  duration: string;
  description: string;
};

export type EducationItem = {
  institution: string;
  degree: string;
  year: string;
};

export type ProjectItem = {
  name: string;
  description: string;
  technologies: string[];
};

export type StructuredResume = {
  name: string | null;
  email: string | null;
  phone: string | null;
  summary: string | null;
  skills: string[];
  experience: ExperienceItem[];
  education: EducationItem[];
  projects: ProjectItem[];
};

export type AnalyzedJD = {
  role: string | null;
  seniority: string | null;
  requiredSkills: string[];
  preferredSkills: string[];
  atsKeywords: string[];
  responsibilities: string[];
};

export type MatchScore = {
  score: number;
  skillScore: number;
  keywordScore: number;
  experienceScore: number;
};

export type GapAnalysis = {
  matchedSkills: string[];
  missingSkills: string[];
  recommendations: string[];
};

export type UploadStepData = {
  rawText: string;
  resume: StructuredResume;
};

export type JDStepData = {
  jobDescription: string;
  analyzedJD: AnalyzedJD;
};

export type AnalysisResult = {
  matchScore: MatchScore;
  gapAnalysis: GapAnalysis;
  customizedResume: StructuredResume;
  suggestions: string[];
  diff: ResumeDiff;
};
