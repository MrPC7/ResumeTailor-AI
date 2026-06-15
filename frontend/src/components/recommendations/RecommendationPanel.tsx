"use client";

import { useCallback, useMemo, useState } from "react";
import { Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ATSGainSummary } from "@/components/recommendations/ATSGainSummary";
import { RecommendationToolbar } from "@/components/recommendations/RecommendationToolbar";
import { RecommendationGroupCard } from "@/components/recommendations/RecommendationGroupCard";
import type { RecommendationReport } from "@/features/workflow/types/workflow.types";

type Props = {
  report: RecommendationReport;
  currentScore: number;
  potentialScore: number;
  selectedIds: Record<string, boolean>;
  onSelectionChange: (next: Record<string, boolean>) => void;
};

export function RecommendationPanel({
  report,
  currentScore,
  potentialScore,
  selectedIds,
  onSelectionChange,
}: Props) {
  const [searchQuery, setSearchQuery] = useState("");
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  // ── Derived counts ────────────────────────────────────────────────
  const allRecIds = useMemo(
    () => report.groups.flatMap((g) => g.recommendations.map((r) => r.id)),
    [report],
  );

  const totalCount = allRecIds.length;
  const selectedCount = useMemo(
    () => allRecIds.filter((id) => selectedIds[id]).length,
    [allRecIds, selectedIds],
  );

  const selectedGain = useMemo(
    () =>
      report.groups
        .flatMap((g) => g.recommendations)
        .filter((r) => selectedIds[r.id])
        .reduce((sum, r) => sum + r.estimatedPoints, 0),
    [report, selectedIds],
  );

  // ── Handlers ──────────────────────────────────────────────────────
  const handleToggleItem = useCallback(
    (id: string) => {
      onSelectionChange({ ...selectedIds, [id]: !selectedIds[id] });
    },
    [selectedIds, onSelectionChange],
  );

  const handleSelectAll = useCallback(() => {
    const next = { ...selectedIds };
    for (const id of allRecIds) next[id] = true;
    onSelectionChange(next);
  }, [allRecIds, selectedIds, onSelectionChange]);

  const handleDeselectAll = useCallback(() => {
    const next = { ...selectedIds };
    for (const id of allRecIds) next[id] = false;
    onSelectionChange(next);
  }, [allRecIds, selectedIds, onSelectionChange]);

  const handleToggleGroupSelection = useCallback(
    (groupId: string) => {
      const group = report.groups.find((g) => g.groupId === groupId);
      if (!group) return;
      const ids = group.recommendations.map((r) => r.id);
      const allGroupSelected = ids.every((id) => selectedIds[id]);
      const next = { ...selectedIds };
      for (const id of ids) next[id] = !allGroupSelected;
      onSelectionChange(next);
    },
    [report, selectedIds, onSelectionChange],
  );

  const handleToggleCollapse = useCallback((groupId: string) => {
    setCollapsedGroups((prev) => ({ ...prev, [groupId]: !prev[groupId] }));
  }, []);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Zap className="h-4 w-4 text-amber-500" />
          AI Recommendations
        </CardTitle>
        <CardDescription>
          Select the recommendations you want to apply. Your projected score updates live.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Live score summary */}
        <ATSGainSummary
          currentScore={currentScore}
          potentialScore={potentialScore}
          selectedGain={selectedGain}
        />

        {/* Toolbar: search + select/deselect all */}
        <RecommendationToolbar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          totalCount={totalCount}
          selectedCount={selectedCount}
          onSelectAll={handleSelectAll}
          onDeselectAll={handleDeselectAll}
        />

        {/* Groups */}
        <div className="space-y-3">
          {report.groups.map((group) => (
            <RecommendationGroupCard
              key={group.groupId}
              group={group}
              selectedIds={selectedIds}
              collapsed={collapsedGroups[group.groupId] ?? false}
              onToggleItem={handleToggleItem}
              onToggleCollapse={() => handleToggleCollapse(group.groupId)}
              onToggleGroupSelection={() => handleToggleGroupSelection(group.groupId)}
              searchQuery={searchQuery}
            />
          ))}
        </div>

        {/* Empty search state */}
        {searchQuery &&
          report.groups.every((g) =>
            g.recommendations.every(
              (r) =>
                !r.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
                !r.description.toLowerCase().includes(searchQuery.toLowerCase()),
            ),
          ) && (
            <p className="text-center text-sm text-slate-400 py-4">
              No recommendations match &ldquo;{searchQuery}&rdquo;
            </p>
          )}
      </CardContent>
    </Card>
  );
}
