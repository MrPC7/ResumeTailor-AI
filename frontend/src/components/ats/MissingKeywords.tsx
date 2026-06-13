"use client";

import { XCircle } from "lucide-react";

type Props = {
  keywords: string[];
};

export function MissingKeywords({ keywords }: Props) {
  if (keywords.length === 0) {
    return (
      <p className="text-sm text-slate-400 italic">
        Great — no missing keywords detected!
      </p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {keywords.map((kw) => (
        <span
          key={kw}
          className="inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-700"
        >
          <XCircle className="h-3 w-3 shrink-0" />
          {kw}
        </span>
      ))}
    </div>
  );
}
