import { C } from "./_ledgerColors";

/** S7 "Full Edition" — subscription teaser (or real Stripe link once configured)
 * + the merged final call-to-action. */
export default function FullEditionTeaser() {
  const foundingLink = process.env.NEXT_PUBLIC_STRIPE_LINK_FOUNDING;

  return (
    <div className="border-2 p-10 text-center" style={{ borderColor: C.ink }}>
      <p className="font-ledger-mono text-xs uppercase tracking-widest" style={{ color: C.gold }}>
        The Full Edition
      </p>
      <h2 className="mt-3 font-ledger-serif text-3xl font-bold" style={{ color: C.ink }}>
        Ready to stop guessing?
      </h2>

      {foundingLink ? (
        <>
          <p className="mx-auto mt-3 max-w-md text-sm" style={{ color: C.inkSoft }}>
            Every graded candidate, every day — free and premium tiers side by side.
          </p>
          <a
            href={foundingLink}
            className="mt-6 inline-block border-2 px-8 py-3 text-sm font-semibold uppercase tracking-widest"
            style={{ borderColor: C.ink, background: C.ink, color: C.paper }}
          >
            Join the Founding Run
          </a>
        </>
      ) : (
        <p className="mx-auto mt-3 max-w-md text-sm italic" style={{ color: C.inkSoft }}>
          The founding subscription run opens after the 4-week scorecard is public. Join the
          waitlist below and we&apos;ll email you the day it does.
        </p>
      )}

      <div className="mt-8 flex items-center justify-center gap-4">
        <a
          href="/demo"
          className="border-2 px-7 py-2.5 text-sm font-medium uppercase tracking-widest"
          style={{ borderColor: C.ink, color: C.ink }}
        >
          Read the Free Edition
        </a>
      </div>
    </div>
  );
}
