"use client";

import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function Footer() {
  const { t } = useLanguage();
  return (
    <footer
      className="border-t px-6 py-10"
      style={{ borderColor: "var(--ledger-rule)", background: "var(--ledger-paper)" }}
    >
      <div className="mx-auto max-w-[1200px] flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="font-ledger-mono text-xs" style={{ color: "var(--ledger-ink-soft)" }}>
          © {new Date().getFullYear()} FinPilot · Vienna, Austria
        </p>
        <p className="text-[10px] max-w-md text-center sm:text-right" style={{ color: "var(--ledger-ink-soft)" }}>
          {t("footer.notAdvice")}
        </p>
      </div>
    </footer>
  );
}
