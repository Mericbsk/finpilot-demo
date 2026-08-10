import { TERMS } from "@/lib/terms";
import type { LedgerCandidate, LedgerConcept } from "@/lib/ledgerSnapshot";
import { candidateRationale } from "@/lib/candidateText";
import { C } from "./_ledgerColors";

const PREVIEW_TERMS = ["squeeze", "calibration", "risk-reward"];

/** S6 "Classroom Preview" — 3 static lesson cards drawn from the same
 * glossary that powers MarginNote, plus the calibration promise. */
interface ClassroomPreviewProps {
  concept?: LedgerConcept;
  candidate?: LedgerCandidate;
}

export default function ClassroomPreview({ concept, candidate }: ClassroomPreviewProps) {
  const cards = PREVIEW_TERMS.map((key) => TERMS[key]).filter(Boolean);

  if (concept && candidate) {
    return (
      <div className="border p-6" style={{ borderColor: C.rule }}>
        <p className="font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
          Today&apos;s concept
        </p>
        <h3 className="mt-2 font-ledger-serif text-2xl font-bold" style={{ color: C.ink }}>
          {concept.name}
        </h3>
        <p className="mt-2 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
          {concept.line}
        </p>
        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          <div>
            <p className="font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
              Market context
            </p>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
              {candidate.ticker} stood out in today&apos;s edition because {candidateRationale(candidate, "en")}
            </p>
          </div>
          <div>
            <p className="font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
              What to check next time
            </p>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
              Does the price move and its participation tell the same story? What is the alternative explanation?
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        {cards.map((t) => (
          <div key={t.slug} className="border p-6" style={{ borderColor: C.rule }}>
            <h3 className="font-ledger-serif text-lg font-bold" style={{ color: C.ink }}>
              {t.name}
            </h3>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
              {t.short}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-8 text-center text-sm italic" style={{ color: C.inkSoft }}>
        Calibration is evaluated against observed outcomes and shown only when the sample is sufficient.
        The full scorecard publishes as the history builds.
      </p>
    </div>
  );
}
