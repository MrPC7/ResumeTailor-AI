"use client";

import { useEffect, useRef, useState } from "react";
import { SuggestionList } from "@/components/suggestions";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import { fetchSuggestions } from "@/features/workflow/services/suggestions.service";
import type { SuggestionsStepData } from "@/features/workflow/types/workflow.types";

type Phase = "loading" | "ready" | "error";

export function StepSuggestions() {
  const recruiterData = useWorkflowStore((s) => s.recruiterData);
  const suggestionsData = useWorkflowStore((s) => s.suggestionsData);
  const completeSuggestions = useWorkflowStore((s) => s.completeSuggestions);
  const toggleSuggestion = useWorkflowStore((s) => s.toggleSuggestion);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const navigateTo = useWorkflowStore((s) => s.navigateTo);

  const [phase, setPhase] = useState<Phase>(suggestionsData ? "ready" : "loading");
  const startedRef = useRef(false);

  useEffect(() => {
    if (suggestionsData || startedRef.current) return;
    if (!recruiterData) return;

    startedRef.current = true;

    async function run() {
      try {
        const result = await fetchSuggestions(recruiterData!);

        const stepData: SuggestionsStepData = {
          suggestions: result.suggestions.suggestions,
          total_count: result.suggestions.total_count,
          critical_count: result.suggestions.critical_count,
          high_count: result.suggestions.high_count,
          selectedSuggestions: Object.fromEntries(
            result.suggestions.suggestions.map((s) => [s.id, true])
          ),
        };

        completeSuggestions(stepData);
        setPhase("ready");
      } catch {
        setPhase("error");
      }
    }

    void run();
  }, [recruiterData, suggestionsData, completeSuggestions]);

  if (phase === "loading") {
    return (
      <div className="flex flex-col items-center justify-center py-16" aria-busy="true">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-indigo-600" />
        <p className="mt-4 text-sm text-slate-500">Generating improvement suggestions...</p>
        <p className="mt-1 text-xs text-slate-400">Analyzing gaps and opportunities</p>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm font-medium text-red-700">
          Failed to generate suggestions. Please try again.
        </p>
        <button
          onClick={() => {
            startedRef.current = false;
            setPhase("loading");
          }}
          className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          Retry
        </button>
        <button
          onClick={goPrev}
          className="ml-3 rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Go Back
        </button>
      </div>
    );
  }

  if (!suggestionsData) return null;

  const handleSelectAll = () => {
    suggestionsData.suggestions.forEach((s) => {
      if (!suggestionsData.selectedSuggestions[s.id]) {
        toggleSuggestion(s.id);
      }
    });
  };

  const handleDeselectAll = () => {
    suggestionsData.suggestions.forEach((s) => {
      if (suggestionsData.selectedSuggestions[s.id]) {
        toggleSuggestion(s.id);
      }
    });
  };

  const selectedCount = Object.values(suggestionsData.selectedSuggestions).filter(Boolean).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4">
        <h2 className="text-sm font-medium text-indigo-700">
          Select the suggestions you want to apply to your resume
        </h2>
        <p className="mt-1 text-xs text-indigo-600">
          {suggestionsData.critical_count > 0 && `${suggestionsData.critical_count} critical • `}
          {suggestionsData.high_count > 0 && `${suggestionsData.high_count} high priority • `}
          {suggestionsData.total_count} total suggestions
        </p>
      </div>

      {/* Suggestion list */}
      <SuggestionList
        suggestions={suggestionsData.suggestions}
        selections={suggestionsData.selectedSuggestions}
        onToggle={toggleSuggestion}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
      />

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={goPrev}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          ← Back
        </button>
        <button
          onClick={() => navigateTo("preview")}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Continue with {selectedCount} selected →
        </button>
      </div>
    </div>
  );
}
