"use client";

import { C } from "./_ledgerColors";
import { useLanguage } from "@/lib/i18n/LanguageContext";

/** Translated section eyebrow heading — a client component so it can read
 * the current language, even though the page around it is server-rendered. */
export default function SectionHeading({ textKey }: { textKey: string }) {
  const { t } = useLanguage();
  return (
    <h2 className="mb-6 font-ledger-mono text-xs uppercase tracking-[0.3em]" style={{ color: C.gold }}>
      {t(textKey)}
    </h2>
  );
}
