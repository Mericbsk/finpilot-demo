"use client";

import GradeSeal from "./GradeSeal";
import MarginNote from "./MarginNote";
import { C } from "./_ledgerColors";
import type { LedgerCandidate } from "@/lib/ledgerSnapshot";
import { candidateRationale } from "@/lib/candidateText";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface EditionArticleProps {
  dateLabel: string;
  contextLine?: string;
  candidates: LedgerCandidate[];
}

const BADGE_LABEL: Record<string, string> = {
  early_tier: "early-detection ladder",
  regime: "regime tailwind",
  momentum: "momentum",
  contraction: "range contraction",
  squeeze: "short squeeze",
  catalyst: "catalyst",
};

/** S2 "Yesterday's Edition" — editorial write-up of yesterday's graded candidates. */
export default function EditionArticle({ dateLabel, contextLine, candidates }: EditionArticleProps) {
  const { lang } = useLanguage();
  if (candidates.length === 0) {
    return (
      <p className="ledger-dropcap text-lg leading-relaxed" style={{ color: C.inkSoft }}>
        No graded candidates cleared the bar in the {dateLabel} edition. Quiet tape, quiet ledger —
        we would rather print nothing than print noise.
      </p>
    );
  }

  const [lede, ...rest] = candidates;

  return (
    <article className="space-y-6">
      {contextLine && (
        <p className="font-ledger-mono text-xs uppercase tracking-widest" style={{ color: C.inkSoft }}>
          {contextLine}
        </p>
      )}

      <div className="flex items-start gap-4">
        <GradeSeal grade={lede.grade} size="lg" />
        <div>
          <p className="ledger-dropcap text-lg leading-relaxed" style={{ color: C.ink }}>
            <span className="font-semibold">{lede.ticker}</span>
            {lede.company ? ` (${lede.company})` : ""} led the {dateLabel} edition.{" "}
            {candidateRationale(lede, lang)}
          </p>
          {lede.badges && lede.badges.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 font-ledger-mono text-xs uppercase tracking-widest">
              {lede.badges.map((b) => (
                <MarginNote key={b} termKey={b} label={BADGE_LABEL[b] ?? b} />
              ))}
            </div>
          )}
        </div>
      </div>

      {rest.length > 0 && (
        <ul className="space-y-4 border-t pt-6" style={{ borderColor: C.rule }}>
          {rest.map((c) => (
            <li key={c.ticker} className="flex items-start gap-4">
              <GradeSeal grade={c.grade} size="sm" />
              <p className="text-sm leading-relaxed" style={{ color: C.inkSoft }}>
                <span className="font-semibold" style={{ color: C.ink }}>
                  {c.ticker}
                </span>{" "}
                {candidateRationale(c, lang)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
