"use client";

import { C } from "./_ledgerColors";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const CREDENTIALS = [
  "Trained on real market data",
  "Reads market mood",
  "Independent votes, no single point of failure",
  "Smart position sizing",
  "Stress-tested before publishing",
  "Daily Telegram alerts",
];

/** Editorial Stance band (between S6 and S7) — reskin of the old HeroGrid
 * "Differentiator" section: the masthead's editorial position + credentials. */
export default function EditorialStance() {
  const { t } = useLanguage();
  return (
    <div className="border-y-2 py-14 text-center" style={{ borderColor: C.ink }}>
      <p className="mb-5 font-ledger-mono text-[10px] uppercase tracking-[0.25em]" style={{ color: C.gold }}>
        {t("editorial.eyebrow")}
      </p>
      <h2 className="mx-auto max-w-3xl font-ledger-serif text-2xl font-bold leading-snug sm:text-3xl" style={{ color: C.ink }}>
        FinPilot isn&apos;t a chatbot wearing a trading costume.
        <br />
        <span className="italic" style={{ color: C.inkSoft }}>
          It runs its own trained models that learn from real market data — not from prompts.
        </span>
      </h2>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {CREDENTIALS.map((tag) => (
          <span
            key={tag}
            className="border px-4 py-1.5 font-ledger-mono text-[11px] uppercase tracking-wide"
            style={{ borderColor: C.rule, color: C.inkSoft }}
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
