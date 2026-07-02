"use client";

import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { SuggestionList } from "@/components/suggestions";
import { customizeResume } from "@/features/workflow/services/customize-resume.service";
import { resumeToText } from "@/features/workflow/services/resume-text.service";
import { runReevaluation } from "@/features/workflow/services/reevaluate.service";
import { useWorkflowStore } from "@/features/workflow/store/workflow.store";
import type { SuggestionsStepData } from "@/features/workflow/types/workflow.types";

export function StepSuggestions() {
  const uploadData = useWorkflowStore((s) => s.uploadData);
  const jdData = useWorkflowStore((s) => s.jdData);
  const recruiterData = useWorkflowStore((s) => s.recruiterData);
  const suggestionsData = useWorkflowStore((s) => s.suggestionsData);
  const setSuggestionsData = useWorkflowStore((s) => s.setSuggestionsData);
  const completeSuggestions = useWorkflowStore((s) => s.completeSuggestions);
  const completePreview = useWorkflowStore((s) => s.completePreview);
  const toggleSuggestion = useWorkflowStore((s) => s.toggleSuggestion);
  const goPrev = useWorkflowStore((s) => s.goPrev);
  const navigateTo = useWorkflowStore((s) => s.navigateTo);

  const initializedRef = useRef(false);

  useEffect(() => {
    if (suggestionsData || initializedRef.current) return;
    if (!recruiterData) return;

    initializedRef.current = true;

    const suggestions = recruiterData.evaluation.suggestions ?? [];
    const criticalCount = suggestions.filter((s) => s.priority === "critical").length;
    const highCount = suggestions.filter((s) => s.priority === "high").length;

    const stepData: SuggestionsStepData = {
      suggestions,
      total_count: suggestions.length,
      critical_count: criticalCount,
      high_count: highCount,
      selectedSuggestions: Object.fromEntries(suggestions.map((s) => [s.id, true])),
    };

    setSuggestionsData(stepData);
  }, [recruiterData, suggestionsData, setSuggestionsData]);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!uploadData || !jdData || !suggestionsData) {
        throw new Error("Workflow data is incomplete.");
      }

      const selectedSuggestionIds = Object.entries(suggestionsData.selectedSuggestions)
        .filter(([, selected]) => selected)
        .map(([id]) => id);

      const customization = await customizeResume(
        uploadData.resume,
        jdData.analyzedJD,
        selectedSuggestionIds,
        suggestionsData.suggestions
      );
      const reevaluation = await runReevaluation(
        uploadData.rawText,
        resumeToText(customization.customizedResume),
        jdData.jobDescription
      );

      return {
        customizedResume: customization.customizedResume,
        reevaluation,
      };
    },
    onSuccess: (data) => {
      if (!suggestionsData) return;
      completeSuggestions(suggestionsData);
      completePreview(data);
      navigateTo("preview");
    },
  });

  if (!suggestionsData) {
    return (
      <div className="flex flex-col items-center justify-center py-16" aria-busy="true">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-indigo-600" />
        <p className="mt-4 text-sm text-slate-500">Loading suggestions...</p>
      </div>
    );
  }

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
  const isApplying = mutation.isPending;

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4">
        <h2 className="text-sm font-medium text-indigo-700">
          Select the suggestions you want to apply to your resume
        </h2>
        <p className="mt-1 text-xs text-indigo-600">
          {suggestionsData.critical_count > 0 && `${suggestionsData.critical_count} critical - `}
          {suggestionsData.high_count > 0 && `${suggestionsData.high_count} high priority - `}
          {suggestionsData.total_count} total suggestions
        </p>
      </div>

      <SuggestionList
        suggestions={suggestionsData.suggestions}
        selections={suggestionsData.selectedSuggestions}
        onToggle={toggleSuggestion}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
      />

      {mutation.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-700">
            Failed to apply improvements. Please try again.
          </p>
        </div>
      )}

      <div className="flex justify-between">
        <button
          onClick={goPrev}
          disabled={isApplying}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Back
        </button>
        <button
          onClick={() => mutation.mutate()}
          disabled={isApplying}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isApplying
            ? "Applying selected improvements..."
            : `Apply Selected Improvements (${selectedCount})`}
        </button>
      </div>
    </div>
  );
}
