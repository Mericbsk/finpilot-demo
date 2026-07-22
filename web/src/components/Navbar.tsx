"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import LanguageSwitcher from "./ledger/LanguageSwitcher";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { t } = useLanguage();

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl border-b"
      style={{ background: "color-mix(in srgb, var(--ledger-paper) 85%, transparent)", borderColor: "var(--ledger-rule)" }}
    >
      <div className="mx-auto flex h-12 max-w-[1200px] items-center justify-between px-6">
        <Link href="/" className="font-ledger-serif text-[16px] font-bold tracking-tight" style={{ color: "var(--ledger-ink)" }}>
          The FinPilot <span style={{ color: "var(--ledger-gold)" }}>Ledger</span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          <a href="#how-its-made" className="text-xs" style={{ color: "var(--ledger-ink-soft)" }}>
            {t("nav.howItsMade")}
          </a>
          <a href="/demo" className="text-xs" style={{ color: "var(--ledger-ink-soft)" }}>
            {t("nav.demo")}
          </a>
          <a href="/dashboard/scanner" className="text-xs" style={{ color: "var(--ledger-ink-soft)" }}>
            Scanner
          </a>
          <LanguageSwitcher />
          <a
            href="/demo"
            className="text-xs px-4 py-1.5 border font-medium uppercase tracking-widest"
            style={{ borderColor: "var(--ledger-ink)", background: "var(--ledger-ink)", color: "var(--ledger-paper)" }}
          >
            {t("nav.readEdition")}
          </a>
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="md:hidden p-1"
          style={{ color: "var(--ledger-ink)" }}
          aria-label="Menu"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            {open
              ? <><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>
              : <><line x1="4" y1="7" x2="20" y2="7" /><line x1="4" y1="12" x2="20" y2="12" /><line x1="4" y1="17" x2="20" y2="17" /></>
            }
          </svg>
        </button>
      </div>

      {open && (
        <div
          className="md:hidden px-6 py-3 border-t space-y-2"
          style={{ background: "var(--ledger-paper)", borderColor: "var(--ledger-rule)" }}
        >
          <a href="#how-its-made" onClick={() => setOpen(false)} className="block text-sm" style={{ color: "var(--ledger-ink-soft)" }}>
            {t("nav.howItsMade")}
          </a>
          <a href="/demo" onClick={() => setOpen(false)} className="block text-sm" style={{ color: "var(--ledger-ink-soft)" }}>
            {t("nav.demo")}
          </a>
          <a href="/dashboard/scanner" onClick={() => setOpen(false)} className="block text-sm" style={{ color: "var(--ledger-ink-soft)" }}>
            Scanner
          </a>
          <div className="pt-1">
            <LanguageSwitcher />
          </div>
          <a href="/demo" onClick={() => setOpen(false)} className="block text-sm pt-1" style={{ color: "var(--ledger-gold)" }}>
            {t("nav.readEdition")} →
          </a>
        </div>
      )}
    </nav>
  );
}
