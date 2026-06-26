export type SuggestionPriority = "critical" | "high" | "medium" | "low";

export type Suggestion = {
  id: string;
  title: string;
  description: string;
  priority: string;
  estimated_impact: string;
  affected_section: string;
};

export type SuggestionReport = {
  suggestions: Suggestion[];
  total_count: number;
  critical_count: number;
  high_count: number;
};
