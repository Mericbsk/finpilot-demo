"use client";

import { useState } from "react";
import { TERMS } from "@/lib/terms";
import type { LedgerCandidate, LedgerConcept } from "@/lib/ledgerSnapshot";
import { candidateRationale, candidateRiskNote } from "@/lib/candidateText";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { C } from "./_ledgerColors";
import GradeSeal from "./GradeSeal";

const PREVIEW_TERMS = ["squeeze", "calibration", "risk-reward"];

const GRADE_RANK: Record<string, number> = { A: 3, B: 2, C: 1 };
const GRADES: Array<"A" | "B" | "C"> = ["A", "B", "C"];

/** S6 "Classroom" — Calibration v0 (2026-08-11).
 *
 * FinSense is not a course to read; it is a mirror on how the reader
 * already thinks. This block asks the reader to commit to a Grade guess
 * BEFORE revealing FinPilot's own Grade for the same candidate, then shows
 * the gap without judging it. Deliberately scoped to what today's snapshot
 * already carries (ticker/company/grade/rationale/risk_note) — no factor
 * weights, no outcome data, because the snapshot contract does not carry
 * those yet. The running count is session-only React state: nothing is
 * persisted, sent to a server, or remembered across visits, and the copy
 * says so — no calibration-history claim we cannot back up.
 *
 * Honesty note: the same candidate's Grade is already printed higher up
 * the page (Yesterday's Edition, The Daily Double), so this is a practice
 * rep, not a blind test — the copy says that too.
 */
interface ClassroomPreviewProps {
  concept?: LedgerConcept;
  candidate?: LedgerCandidate;
}

export default function ClassroomPreview({ concept, candidate }: ClassroomPreviewProps) {
  const { lang } = useLanguage();
  const [guess, setGuess] = useState<"A" | "B" | "C" | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [tally, setTally] = useState({ attempts: 0, matches: 0 });

  const cards = PREVIEW_TERMS.map((key) => TERMS[key]).filter(Boolean);

  if (concept && candidate) {
    const actualGrade = candidate.grade in GRADE_RANK ? candidate.grade : null;

    const handleCommit = (g: "A" | "B" | "C") => {
      if (revealed) return;
      setGuess(g);
    };

    const handleReveal = () => {
      if (!guess || revealed) return;
      setRevealed(true);
      if (actualGrade) {
        setTally((t) => ({
          attempts: t.attempts + 1,
          matches: t.matches + (guess === actualGrade ? 1 : 0),
        }));
      }
    };

    const handleReset = () => {
      setGuess(null);
      setRevealed(false);
    };

    let verdict: string | null = null;
    if (revealed && guess && actualGrade) {
      if (guess === actualGrade) {
        verdict = "You matched FinPilot's Grade — same read, reached independently.";
      } else if (GRADE_RANK[guess] > GRADE_RANK[actualGrade]) {
        verdict = "You were more confident than FinPilot's Grade. Worth asking: what did you weigh that the rules didn't?";
      } else {
        verdict = "You were more cautious than FinPilot's Grade. Worth asking: what risk were you pricing in that the rules didn't catch?";
      }
    }

    return (
      <div className="space-y-6">
        <p className="text-sm leading-relaxed" style={{ color: C.inkSoft }}>
          FinSense in one line: not a lesson to read, but a mirror on how you already think about
          the market. Guess first, then compare — the gap is more informative than the grade.
        </p>

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
        </div>

        <div className="border p-6" style={{ borderColor: C.rule }}>
          <p className="font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
            Calibration practice — this session only, nothing saved
          </p>
          <p className="mt-2 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
            <span className="font-semibold" style={{ color: C.ink }}>{candidate.ticker}</span>
            {candidate.company ? ` (${candidate.company})` : ""} stood out in today&apos;s edition
            because {candidateRationale(candidate, lang)}
          </p>
          <p className="mt-2 text-xs italic leading-relaxed" style={{ color: C.inkSoft }}>
            You may have already seen this candidate&apos;s Grade higher up the page — this is a
            practice rep, not a blind test. For the real version, guess before you scroll past
            tomorrow&apos;s edition.
          </p>

          {!revealed && (
            <div className="mt-4">
              <p className="text-xs uppercase tracking-widest" style={{ color: C.inkSoft }}>
                Before you check: what Grade would you call this?
              </p>
              <div className="mt-3 flex gap-3">
                {GRADES.map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => handleCommit(g)}
                    className="flex h-11 w-11 items-center justify-center rounded-full border-2 font-ledger-mono text-xs font-bold uppercase tracking-wider transition"
                    style={{
                      borderColor: guess === g ? C.gold : C.rule,
                      background: guess === g ? C.gold : "transparent",
                      color: guess === g ? C.paper : C.ink,
                    }}
                  >
                    {g}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={handleReveal}
                disabled={!guess}
                className="mt-4 font-ledger-mono text-[10px] uppercase tracking-widest underline disabled:no-underline disabled:opacity-40"
                style={{ color: guess ? C.gold : C.inkSoft }}
              >
                Reveal FinPilot&apos;s Grade →
              </button>
            </div>
          )}

          {revealed && actualGrade && (
            <div className="mt-4 border-t pt-4" style={{ borderColor: C.rule }}>
              <div className="flex items-start gap-3">
                <GradeSeal grade={actualGrade} size="sm" />
                <div>
                  <p className="text-sm leading-relaxed" style={{ color: C.inkSoft }}>
                    FinPilot called it <span className="font-semibold" style={{ color: C.ink }}>Grade {actualGrade}</span>.
                    You guessed <span className="font-semibold" style={{ color: C.ink }}>Grade {guess}</span>.
                  </p>
                  {(candidate.risk_note || candidate.risk_note_i18n) && (
                    <p className="mt-1 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
                      {candidateRiskNote(candidate, lang)}
                    </p>
                  )}
                </div>
              </div>
              {verdict && (
                <p className="mt-3 text-sm leading-relaxed" style={{ color: C.ink }}>
                  {verdict}
                </p>
              )}
              <div className="mt-3 flex items-center justify-between">
                <p className="font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.inkSoft }}>
                  This session: {tally.matches}/{tally.attempts} matched
                </p>
                <button
                  type="button"
                  onClick={handleReset}
                  className="font-ledger-mono text-[10px] uppercase tracking-widest underline"
                  style={{ color: C.gold }}
                >
                  Try another guess
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div>
      <p className="mb-6 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
        FinSense in one line: not a lesson to read, but a mirror on how you already think about
        the market. When today&apos;s edition is live, this section turns into a practice
        rep — guess a candidate&apos;s Grade before you see it, then compare.
      </p>
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
