"use client";

import Waitlist from "@/components/Waitlist";
import { C } from "./_ledgerColors";
import { useLanguage } from "@/lib/i18n/LanguageContext";

/** S8 "Colophon" — waitlist (existing component, restyled) + the small-print
 * block a real newspaper prints in its colophon: distribution channel,
 * methodology link, disclaimer. */
export default function Colophon() {
  const { t } = useLanguage();
  return (
    <div>
      <Waitlist />
      <div className="mx-auto max-w-2xl border-t px-6 py-10 text-center" style={{ borderColor: C.rule }}>
        <p className="text-sm" style={{ color: C.inkSoft }}>
          {t("colophon.follow")}{" "}
          <a
            href="https://t.me/Finpilot_Breif"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold underline"
            style={{ color: C.gold }}
          >
            {t("colophon.telegram")}
          </a>
          {" · "}
          <a href="/methodology" className="font-semibold underline" style={{ color: C.gold }}>
            Methodology
          </a>
        </p>
        <p className="mt-4 text-xs" style={{ color: C.inkSoft }}>
          {t("colophon.disclaimer")}
        </p>
      </div>
    </div>
  );
}
