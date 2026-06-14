export type WorkflowStep = "upload" | "jd" | "optimize" | "download";

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

export type ATSScores = {
  skills: number;
  keywords: number;
  experience: number;
  education: number;
  overallFit: number;
};

export type ATSEvaluationResult = {
  overallScore: number;
  confidence: number;
  scores: ATSScores;
  strengths: string[];
  weaknesses: string[];
  missingKeywords: string[];
  recommendedActions: string[];
};

export type ATSComparisonResult = {
  beforeScore: number;
  afterScore: number;
  improvement: number;
  before: ATSEvaluationResult;
  after: ATSEvaluationResult;
};

export type OptimizeResult = {
  customizedResume: StructuredResume;
  atsComparison: ATSComparisonResult;
};
