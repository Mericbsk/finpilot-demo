"use client";

import { C } from "./_ledgerColors";
import GradeSeal from "./GradeSeal";
import type { LedgerCandidate, LedgerConcept } from "@/lib/ledgerSnapshot";
import { candidateRationale } from "@/lib/candidateText";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface DailyDoubleProps {
  concept?: LedgerConcept;
  candidate?: LedgerCandidate;
}

/** S3 "Daily Double" — bridges the day's glossary concept (lesson card) with
 * the case-study candidate it best explains (vaka kartı). */
export default function DailyDouble({ concept, candidate }: DailyDoubleProps) {
  const { lang } = useLanguage();
  if (!concept && !candidate) return null;

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
      {concept && (
        <div className="border p-6" style={{ borderColor: C.rule }}>
          <p className="mb-2 font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
            Today&apos;s Lesson
          </p>
          <h3 className="font-ledger-serif text-lg font-bold" style={{ color: C.ink }}>
            {concept.name}
          </h3>
          <p className="mt-2 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
            {concept.line}
          </p>
        </div>
      )}
      {candidate && (
        <div className="border p-6" style={{ borderColor: C.rule }}>
          <p className="mb-2 font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
            Today&apos;s Case
          </p>
          <div className="flex items-start gap-3">
            <GradeSeal grade={candidate.grade} size="sm" />
            <p className="text-sm leading-relaxed" style={{ color: C.inkSoft }}>
              <span className="font-semibold" style={{ color: C.ink }}>
                {candidate.ticker}
              </span>{" "}
              {candidateRationale(candidate, lang)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
