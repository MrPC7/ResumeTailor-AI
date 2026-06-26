"use client";

import { cn } from "@/lib/utils";
import type { Suggestion } from "./types";
import { SuggestionCard } from "./SuggestionCard";

type Props = {
  suggestions: Suggestion[];
  selections: Record<string, boolean>;
  onToggle: (id: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  className?: string;
};

export function SuggestionList({
  suggestions,
  selections,
  onToggle,
  onSelectAll,
  onDeselectAll,
  className,
}: Props) {
  const selectedCount = Object.values(selections).filter(Boolean).length;
  const totalCount = suggestions.length;

  return (
    <div className={cn("space-y-4", className)} aria-label="Improvement suggestions">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{selectedCount}</span>
          {" of "}
          <span className="font-medium text-foreground">{totalCount}</span>
          {" selected"}
        </p>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onSelectAll}
            disabled={selectedCount === totalCount}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
            aria-label="Select all suggestions"
          >
            Select All
          </button>
          <button
            type="button"
            onClick={onDeselectAll}
            disabled={selectedCount === 0}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
            aria-label="Deselect all suggestions"
          >
            Deselect All
          </button>
        </div>
      </div>

      {/* Cards */}
      <div className="space-y-3" role="group" aria-label="Suggestion checkboxes">
        {suggestions.map((suggestion) => (
          <SuggestionCard
            key={suggestion.id}
            suggestion={suggestion}
            selected={selections[suggestion.id] ?? false}
            onToggle={onToggle}
          />
        ))}
      </div>

      {totalCount === 0 && (
        <p className="py-8 text-center text-sm text-muted-foreground">No suggestions available.</p>
      )}
    </div>
  );
}
