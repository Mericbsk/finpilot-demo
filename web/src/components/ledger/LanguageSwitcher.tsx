"use client";

import { useLanguage } from "@/lib/i18n/LanguageContext";
import { LANGUAGES } from "@/lib/i18n/translations";

/** EN/DE/TR switcher for the Ledger landing/demo chrome. */
export default function LanguageSwitcher() {
  const { lang, setLang } = useLanguage();

  return (
    <div className="flex items-center gap-1 font-ledger-mono text-[11px]">
      {LANGUAGES.map((l, i) => (
        <span key={l.code} className="flex items-center">
          {i > 0 && (
            <span className="mx-1" style={{ color: "var(--ledger-rule)" }}>
              /
            </span>
          )}
          <button
            type="button"
            onClick={() => setLang(l.code)}
            aria-current={lang === l.code}
            className="px-0.5 uppercase tracking-wide transition"
            style={{
              color: lang === l.code ? "var(--ledger-gold)" : "var(--ledger-ink-soft)",
              fontWeight: lang === l.code ? 700 : 400,
            }}
          >
            {l.label}
          </button>
        </span>
      ))}
    </div>
  );
}
