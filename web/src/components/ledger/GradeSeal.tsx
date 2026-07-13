import { C } from "./_ledgerColors";

interface GradeSealProps {
  grade: string;
  size?: "sm" | "md" | "lg";
}

const SEAL_STYLE: Record<string, { bg: string; fg: string; label: string }> = {
  A: { bg: C.gold, fg: C.paper, label: "GRADE A" },
  B: { bg: C.steel, fg: C.paper, label: "GRADE B" },
  C: { bg: C.inkSoft, fg: C.paper, label: "GRADE C" },
};

const SIZE: Record<NonNullable<GradeSealProps["size"]>, string> = {
  sm: "h-8 w-8 text-[9px]",
  md: "h-11 w-11 text-[10px]",
  lg: "h-16 w-16 text-xs",
};

/** A newspaper-style circular "seal" stamping a research grade (A/B/C). */
export default function GradeSeal({ grade, size = "md" }: GradeSealProps) {
  const style = SEAL_STYLE[grade] ?? SEAL_STYLE.C;
  return (
    <div
      className={`inline-flex shrink-0 items-center justify-center rounded-full border-2 font-ledger-mono font-bold uppercase tracking-wider ${SIZE[size]}`}
      style={{ background: style.bg, color: style.fg, borderColor: style.fg + "40" }}
      title={style.label}
    >
      {grade}
    </div>
  );
}
