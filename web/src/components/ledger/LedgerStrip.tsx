import { C } from "./_ledgerColors";
import type { LedgerKarne } from "@/lib/ledgerSnapshot";

interface LedgerStripProps {
  karne: LedgerKarne | null;
}

const GRADE_ORDER = ["A", "B", "C"];
const GRADE_COLOR: Record<string, string> = { A: C.gold, B: C.steel, C: C.inkSoft };

/** S4 "Ledger Strip" — today's grade totals as a heat-strip, plus the
 * historical scorecard (by_grade) when it has actually been compiled. */
export default function LedgerStrip({ karne }: LedgerStripProps) {
  const totals = karne?.toplam_aday_bugun ?? {};
  const grades = GRADE_ORDER.filter((g) => totals[g] != null);
  const max = Math.max(1, ...grades.map((g) => totals[g] ?? 0));
  const hasScorecard = !!karne?.by_grade && Object.keys(karne.by_grade).length > 0;

  if (grades.length === 0) {
    return (
      <p className="text-sm italic" style={{ color: C.inkSoft }}>
        No graded candidates today — the ledger strip is honestly empty rather than padded.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        {grades.map((g) => {
          const n = totals[g] ?? 0;
          const pct = Math.round((n / max) * 100);
          return (
            <div key={g} className="flex items-center gap-3">
              <span className="w-6 font-ledger-mono text-sm font-bold" style={{ color: C.ink }}>
                {g}
              </span>
              <div className="h-3 flex-1 overflow-hidden rounded-none" style={{ background: C.paperDim }}>
                <div className="h-full" style={{ width: `${pct}%`, background: GRADE_COLOR[g] }} />
              </div>
              <span className="w-8 text-right font-ledger-mono text-xs" style={{ color: C.inkSoft }}>
                {n}
              </span>
            </div>
          );
        })}
      </div>

      {hasScorecard ? (
        <div className="border-l-4 pl-4 italic" style={{ borderColor: C.brick, color: C.inkSoft }}>
          Scorecard compiled from {karne?.window || "recent"} grading history — see the full
          methodology for hit-rate definitions.
        </div>
      ) : (
        <p className="border-l-4 pl-4 text-sm italic" style={{ borderColor: C.rule, color: C.inkSoft }}>
          Multi-week scorecard (hit-rate by grade) is still compiling — we print today&apos;s
          totals honestly and will add the historical strip once enough editions have run.
        </p>
      )}
    </div>
  );
}
