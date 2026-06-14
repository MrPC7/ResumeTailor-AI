"use client";

import { CheckCheck, Search, X, XCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type Props = {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  totalCount: number;
  selectedCount: number;
  onSelectAll: () => void;
  onDeselectAll: () => void;
};

export function RecommendationToolbar({
  searchQuery,
  onSearchChange,
  totalCount,
  selectedCount,
  onSelectAll,
  onDeselectAll,
}: Props) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      {/* Search */}
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <Input
          type="text"
          placeholder="Search recommendations..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-9 pl-9 pr-9 text-sm"
        />
        {searchQuery && (
          <button
            type="button"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            onClick={() => onSearchChange("")}
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Bulk actions */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-500 tabular-nums mr-1">
          {selectedCount}/{totalCount}
        </span>
        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-1.5 text-xs"
          onClick={onSelectAll}
          disabled={selectedCount === totalCount}
        >
          <CheckCheck className="h-3.5 w-3.5" />
          Select All
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-1.5 text-xs"
          onClick={onDeselectAll}
          disabled={selectedCount === 0}
        >
          <XCircle className="h-3.5 w-3.5" />
          Deselect All
        </Button>
      </div>
    </div>
  );
}
