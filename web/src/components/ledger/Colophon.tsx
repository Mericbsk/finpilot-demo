import Waitlist from "@/components/Waitlist";
import { C } from "./_ledgerColors";

/** S8 "Colophon" — waitlist (existing component, restyled) + the small-print
 * block a real newspaper prints in its colophon: distribution channel,
 * methodology link, disclaimer. */
export default function Colophon() {
  return (
    <div>
      <Waitlist />
      <div className="mx-auto max-w-2xl border-t px-6 py-10 text-center" style={{ borderColor: C.rule }}>
        <p className="text-sm" style={{ color: C.inkSoft }}>
          Follow the free daily edition on{" "}
          <a
            href="https://t.me/Finpilot_Breif"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold underline"
            style={{ color: C.gold }}
          >
            Telegram
          </a>
          {/* TODO: link to /methodology once that page ships (LAUNCH_CHECKLIST
              Week-2 item) — no dead link in the meantime. */}
        </p>
        <p className="mt-4 text-xs" style={{ color: C.inkSoft }}>
          FinPilot publishes research grades, not investment advice. Every grade is a probability
          estimate, not a guarantee — decisions and risk are always the reader&apos;s own.
        </p>
      </div>
    </div>
  );
}
