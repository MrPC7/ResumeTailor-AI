"use client";

import { CheckCircle2 } from "lucide-react";

type Props = {
  keywords: string[];
};

export function MatchedKeywords({ keywords }: Props) {
  if (keywords.length === 0) {
    return <p className="text-sm italic text-slate-400">No matched keywords found.</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {keywords.map((kw) => (
        <span
          key={kw}
          className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700"
        >
          <CheckCircle2 className="h-3 w-3 shrink-0" />
          {kw}
        </span>
      ))}
    </div>
  );
}
