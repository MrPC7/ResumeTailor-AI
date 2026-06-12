import type { DiffToken as DiffTokenType } from "@/features/resume-diff/types/diff.types";
import { DiffToken } from "@/features/resume-diff/components/DiffToken";

type Props = {
  title: string;
  children: React.ReactNode;
};

export function DiffSection({ title, children }: Props) {
  return (
    <div className="space-y-1">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</h3>
      <div className="rounded-md border border-slate-200 bg-white p-3 text-sm leading-relaxed text-slate-800">
        {children}
      </div>
    </div>
  );
}

type InlineProps = {
  tokens: DiffTokenType[];
};

export function InlineDiff({ tokens }: InlineProps) {
  return (
    <>
      {tokens.map((token, index) => (
        <DiffToken key={index} token={token} />
      ))}
    </>
  );
}
