import type { DiffToken as DiffTokenType } from "@/features/resume-diff/types/diff.types";
import { cn } from "@/lib/utils";

type Props = {
  token: DiffTokenType;
};

const STATUS_CLASSES: Record<DiffTokenType["status"], string> = {
  added: "bg-emerald-100 text-emerald-900 rounded px-0.5",
  removed: "bg-red-100 text-red-900 line-through rounded px-0.5",
  unchanged: "",
};

export function DiffToken({ token }: Props) {
  return (
    <span className={cn("whitespace-pre-wrap", STATUS_CLASSES[token.status])}>{token.text}</span>
  );
}
