"use client";

import { C } from "./_ledgerColors";
import { useLanguage } from "@/lib/i18n/LanguageContext";

/** S7 "Full Edition" — subscription teaser (or real Stripe link once configured)
 * + the merged final call-to-action. */
export default function FullEditionTeaser() {
  const foundingLink = process.env.NEXT_PUBLIC_STRIPE_LINK_FOUNDING;
  const { t } = useLanguage();

  return (
    <div className="border-2 p-10 text-center" style={{ borderColor: C.ink }}>
      <p className="font-ledger-mono text-xs uppercase tracking-widest" style={{ color: C.gold }}>
        {t("fullEdition.eyebrow")}
      </p>
      <h2 className="mt-3 font-ledger-serif text-3xl font-bold" style={{ color: C.ink }}>
        {t("fullEdition.headline")}
      </h2>

      {foundingLink ? (
        <>
          <p className="mx-auto mt-3 max-w-md text-sm" style={{ color: C.inkSoft }}>
            {t("fullEdition.teaserBefore")}
          </p>
          <a
            href={foundingLink}
            className="mt-6 inline-block border-2 px-8 py-3 text-sm font-semibold uppercase tracking-widest"
            style={{ borderColor: C.ink, background: C.ink, color: C.paper }}
          >
            {t("fullEdition.ctaJoin")}
          </a>
        </>
      ) : (
        <p className="mx-auto mt-3 max-w-md text-sm italic" style={{ color: C.inkSoft }}>
          {t("fullEdition.teaserAfter")}
        </p>
      )}

      <div className="mt-8 flex items-center justify-center gap-4">
        <a
          href="/demo"
          className="border-2 px-7 py-2.5 text-sm font-medium uppercase tracking-widest"
          style={{ borderColor: C.ink, color: C.ink }}
        >
          {t("fullEdition.ctaReadFree")}
        </a>
      </div>
    </div>
  );
}
