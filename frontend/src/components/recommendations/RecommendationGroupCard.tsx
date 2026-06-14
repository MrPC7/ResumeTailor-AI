"use client";

import { useMemo } from "react";
import { Check, ChevronDown, ChevronRight, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { RecommendationItem } from "@/components/recommendations/RecommendationItem";
import type { RecommendationGroup } from "@/features/workflow/types/workflow.types";

type Props = {
  group: RecommendationGroup;
  selectedIds: Record<string, boolean>;
  collapsed: boolean;
  onToggleItem: (id: string) => void;
  onToggleCollapse: () => void;
  onToggleGroupSelection: () => void;
  searchQuery?: string;
};

export function RecommendationGroupCard({
  group,
  selectedIds,
  collapsed,
  onToggleItem,
  onToggleCollapse,
  onToggleGroupSelection,
  searchQuery = "",
}: Props) {
  const { groupId, groupTitle, recommendations } = group;

  const selectedCount = useMemo(
    () => recommendations.filter((r) => selectedIds[r.id]).length,
    [recommendations, selectedIds],
  );

  const groupPoints = useMemo(
    () => recommendations.reduce((sum, r) => sum + r.estimatedPoints, 0),
    [recommendations],
  );

  const selectedPoints = useMemo(
    () =>
      recommendations
        .filter((r) => selectedIds[r.id])
        .reduce((sum, r) => sum + r.estimatedPoints, 0),
    [recommendations, selectedIds],
  );

  const allSelected = selectedCount === recommendations.length;
  const someSelected = selectedCount > 0 && !allSelected;

  // Filter by search query
  const visibleRecs = useMemo(() => {
    if (!searchQuery) return recommendations;
    const q = searchQuery.toLowerCase();
    return recommendations.filter(
      (r) =>
        r.title.toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q) ||
        r.impactLevel.includes(q),
    );
  }, [recommendations, searchQuery]);

  if (searchQuery && visibleRecs.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
      {/* Group header */}
      <div className="flex items-center gap-2 px-4 py-3 bg-slate-50/60 border-b border-slate-100">
        {/* Group checkbox */}
        <button
          type="button"
          className={cn(
            "flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded border-2 transition-colors",
            allSelected
              ? "border-emerald-600 bg-emerald-600 text-white"
              : someSelected
                ? "border-emerald-400 bg-emerald-100 text-emerald-600"
                : "border-slate-300 bg-white hover:border-slate-400",
          )}
          onClick={(e) => {
            e.stopPropagation();
            onToggleGroupSelection();
          }}
          aria-label={allSelected ? `Deselect all in ${groupTitle}` : `Select all in ${groupTitle}`}
        >
          {allSelected && <Check className="h-3 w-3" />}
          {someSelected && <Minus className="h-3 w-3" />}
        </button>

        {/* Collapse toggle + title */}
        <button
          type="button"
          className="flex flex-1 items-center gap-2 text-left"
          onClick={onToggleCollapse}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          )}
          <span className="text-sm font-semibold text-slate-800">{groupTitle}</span>
          <span className="text-xs text-slate-400 tabular-nums">
            {selectedCount}/{recommendations.length}
          </span>
        </button>

        {/* Points summary */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold tabular-nums text-blue-600">
            +{selectedPoints}/{groupPoints} pts
          </span>
        </div>
      </div>

      {/* Recommendations */}
      {!collapsed && (
        <div className="space-y-1.5 p-3">
          {visibleRecs.map((rec) => (
            <RecommendationItem
              key={rec.id}
              recommendation={rec}
              checked={selectedIds[rec.id] ?? false}
              onToggle={onToggleItem}
              highlighted={!!searchQuery}
            />
          ))}
        </div>
      )}
    </div>
  );
}
