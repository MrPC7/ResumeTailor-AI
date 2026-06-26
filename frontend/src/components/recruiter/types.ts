export type RecruiterEvaluation = {
  match_level: string;
  hiring_confidence: number;
  interview_probability: number;
  strengths: string[];
  gaps: string[];
  verdict: string;
  reasoning: string[];
};

export type ImprovementMetrics = {
  hiring_confidence_delta: number;
  interview_probability_delta: number;
  gaps_before: number;
  gaps_after: number;
  gaps_reduced: number;
  strengths_before: number;
  strengths_after: number;
  strengths_gained: number;
  match_level_before: string;
  match_level_after: string;
  improved: boolean;
};

export type ReevaluationResult = {
  before: RecruiterEvaluation;
  after: RecruiterEvaluation;
  improvement: ImprovementMetrics;
};

export type EvaluateResponse = {
  candidateProfile: {
    skills: { name: string; category: string }[];
    work_experience: {
      company: string;
      position: string;
      duration: string;
      responsibilities: string[];
      technologies: string[];
    }[];
    education: {
      institution: string;
      degree: string;
      field_of_study: string;
      year: string;
    }[];
    projects: {
      name: string;
      description: string;
      technologies: string[];
      role: string;
    }[];
    certifications: {
      name: string;
      issuer: string;
      year: string;
    }[];
    total_years_experience: number | null;
    primary_domain: string;
  };
  jobProfile: {
    role: string;
    seniority: string;
    must_have_skills: { name: string; category: string }[];
    preferred_skills: { name: string; category: string }[];
    responsibilities: { description: string; priority: string }[];
    experience_required: {
      min_years: number | null;
      max_years: number | null;
      domain: string;
    };
  };
  evaluation: RecruiterEvaluation;
};
