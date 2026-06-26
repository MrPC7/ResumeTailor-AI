export type WorkflowStep = "upload" | "jd" | "recruiter" | "suggestions" | "preview" | "download";

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
  matchedKeywords: string[];
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

export type PotentialScoreResult = {
  currentScore: number;
  potentialScore: number;
  improvementPotential: number;
};

export type ImpactLevel = "critical" | "high" | "medium" | "low";

export type Recommendation = {
  id: string;
  title: string;
  description: string;
  impactLevel: ImpactLevel;
  estimatedPoints: number;
};

export type RecommendationGroup = {
  groupId: string;
  groupTitle: string;
  recommendations: Recommendation[];
};

export type RecommendationReport = {
  totalEstimatedGain: number;
  groups: RecommendationGroup[];
};

export type ATSStepData = {
  atsResult: ATSEvaluationResult;
  potentialScore: PotentialScoreResult | null;
  recReport: RecommendationReport | null;
  selectedRecommendations: Record<string, boolean>;
};

export type OptimizeResult = {
  customizedResume: StructuredResume;
  atsComparison: ATSComparisonResult;
};

export type CoverLetterData = {
  coverLetter: string;
  strengthsHighlighted: string[];
  matchingSkillsUsed: string[];
};

export type RecruiterStepData = {
  candidateProfile: {
    skills: { name: string; category: string }[];
    work_experience: {
      company: string;
      position: string;
      duration: string;
      responsibilities: string[];
      technologies: string[];
    }[];
    total_years_experience: number | null;
    primary_domain: string;
  };
  jobProfile: {
    role: string;
    seniority: string;
    must_have_skills: { name: string; category: string }[];
    preferred_skills: { name: string; category: string }[];
  };
  evaluation: {
    match_level: string;
    hiring_confidence: number;
    interview_probability: number;
    strengths: string[];
    gaps: string[];
    verdict: string;
    reasoning: string[];
  };
};

export type SuggestionsStepData = {
  suggestions: {
    id: string;
    title: string;
    description: string;
    priority: string;
    estimated_impact: string;
    affected_section: string;
  }[];
  total_count: number;
  critical_count: number;
  high_count: number;
  selectedSuggestions: Record<string, boolean>;
};
