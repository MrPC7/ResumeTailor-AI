"use client";

import { cn } from "@/lib/utils";
import type { Suggestion } from "./types";

type Props = {
  suggestion: Suggestion;
  selected: boolean;
  onToggle: (id: string) => void;
};

function priorityConfig(priority: string) {
  switch (priority) {
    case "critical":
      return {
        label: "Critical",
        badgeClass: "bg-red-100 text-red-700 border-red-200",
        ringClass: "ring-red-200",
      };
    case "high":
      return {
        label: "High",
        badgeClass: "bg-orange-100 text-orange-700 border-orange-200",
        ringClass: "ring-orange-200",
      };
    case "medium":
      return {
        label: "Medium",
        badgeClass: "bg-amber-100 text-amber-700 border-amber-200",
        ringClass: "ring-amber-200",
      };
    case "low":
      return {
        label: "Low",
        badgeClass: "bg-slate-100 text-slate-600 border-slate-200",
        ringClass: "ring-slate-200",
      };
    default:
      return {
        label: priority || "Medium",
        badgeClass: "bg-amber-100 text-amber-700 border-amber-200",
        ringClass: "ring-amber-200",
      };
  }
}

export function SuggestionCard({ suggestion, selected, onToggle }: Props) {
  const config = priorityConfig(suggestion.priority);

  return (
    <label
      htmlFor={`suggestion-${suggestion.id}`}
      className={cn(
        "flex cursor-pointer gap-3 rounded-lg border p-4 transition-all",
        selected
          ? "border-indigo-300 bg-indigo-50 ring-2 ring-indigo-200"
          : "border-slate-200 bg-card hover:border-slate-300 hover:bg-slate-50"
      )}
    >
      {/* Checkbox */}
      <div className="flex-shrink-0 pt-0.5">
        <input
          id={`suggestion-${suggestion.id}`}
          type="checkbox"
          checked={selected}
          onChange={() => onToggle(suggestion.id)}
          className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          aria-label={`Select suggestion: ${suggestion.title}`}
        />
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm font-medium text-foreground">{suggestion.title}</h4>
          <span
            className={cn(
              "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold",
              config.badgeClass
            )}
          >
            {config.label}
          </span>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-600">
            {suggestion.affected_section}
          </span>
        </div>

        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
          {suggestion.description}
        </p>

        <p className="mt-2 text-xs font-medium text-indigo-600">
          Impact: {suggestion.estimated_impact}
        </p>
      </div>
    </label>
  );
}
