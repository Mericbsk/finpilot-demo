"use client";

/**
 * Premium offer page (Funnel doc §8). Ships dark until the 4-week scorecard
 * gate passes; then it is linked from the demo + Telegram.
 * Payment: Stripe Payment Links (env-configured) — no in-app billing code.
 */

import Link from "next/link";
import { ArrowLeft, Check, ShieldCheck } from "lucide-react";

const STRIPE_FOUNDING = process.env.NEXT_PUBLIC_STRIPE_LINK_FOUNDING || "";
const STRIPE_MONTHLY = process.env.NEXT_PUBLIC_STRIPE_LINK_MONTHLY || "";
const TELEGRAM_URL = process.env.NEXT_PUBLIC_TELEGRAM_URL || "https://t.me/finpilot";

const DISCLAIMER =
  "FinPilot is a research and education tool; it does not provide investment advice. Past performance does not guarantee future results.";

const ROWS: [string, string, string][] = [
  ["Morning candidates", "1–2 per day", "Full daily list (Top-3 + Grade B)"],
  ["Rationale", "2 sentences", "Full factor breakdown + risk note"],
  ["Follow-ups on past candidates", "—", "Daily watch updates"],
  ["Weekly deep-dive", "Summary", "Full edge & scorecard analysis"],
  ["Open scorecard", "✓ (always free)", "✓ (always free)"],
];

export default function PremiumPage() {
  return (
    <main className="min-h-screen bg-[#0a0e1a] px-4 py-10">
      <div className="mx-auto max-w-xl space-y-8">
        <div>
          <Link href="/" className="inline-flex items-center gap-1 text-sm text-white/50 hover:text-white">
            <ArrowLeft className="h-4 w-4" /> finpilot.at
          </Link>
          <h1 className="mt-4 text-3xl font-bold text-white">The full brief, every morning.</h1>
          <p className="mt-3 text-[14px] leading-relaxed text-white/60">
            The free brief shows you 1–2 of the day&apos;s candidates. Premium shows you
            everything the system sees — the full graded list, the full reasoning, and the
            risks — delivered to a private Telegram channel at the same 08:30.
          </p>
        </div>

        {/* Comparison table */}
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <div className="grid grid-cols-3 gap-2 bg-white/[0.04] px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-white/50">
            <span />
            <span className="text-center">Free</span>
            <span className="text-center text-violet-300">Premium</span>
          </div>
          {ROWS.map(([label, free, prem]) => (
            <div key={label} className="grid grid-cols-3 gap-2 border-t border-white/5 px-4 py-3 text-[12px]">
              <span className="text-white/70">{label}</span>
              <span className="text-center text-white/50">{free}</span>
              <span className="text-center font-medium text-white">{prem}</span>
            </div>
          ))}
        </div>

        {/* Pricing */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-violet-400/30 bg-violet-500/10 p-5">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-violet-300">
              Founding member · 20 seats, fixed
            </div>
            <div className="mt-2 text-3xl font-bold text-white">
              €99<span className="text-base font-normal text-white/50">/year</span>
            </div>
            <ul className="mt-3 space-y-1.5 text-[13px] text-white/70">
              {["Price locked forever", "Founding badge & product input", "14-day unconditional refund"].map((f) => (
                <li key={f} className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-violet-300" /> {f}
                </li>
              ))}
            </ul>
            {STRIPE_FOUNDING ? (
              <a
                href={STRIPE_FOUNDING}
                className="mt-4 block rounded-xl bg-violet-500/80 py-2.5 text-center text-sm font-semibold text-white hover:bg-violet-500"
              >
                Become a founding member
              </a>
            ) : (
              <div className="mt-4 rounded-xl border border-white/10 py-2.5 text-center text-sm text-white/40">
                Opens after the 4-week public scorecard
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-white/50">Monthly</div>
            <div className="mt-2 text-3xl font-bold text-white">
              €9<span className="text-base font-normal text-white/50">/month</span>
            </div>
            <ul className="mt-3 space-y-1.5 text-[13px] text-white/70">
              {["Cancel anytime, one click", "Same full daily brief", "14-day unconditional refund"].map((f) => (
                <li key={f} className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-white/50" /> {f}
                </li>
              ))}
            </ul>
            {STRIPE_MONTHLY ? (
              <a
                href={STRIPE_MONTHLY}
                className="mt-4 block rounded-xl bg-white/10 py-2.5 text-center text-sm font-semibold text-white hover:bg-white/15"
              >
                Start monthly
              </a>
            ) : (
              <div className="mt-4 rounded-xl border border-white/10 py-2.5 text-center text-sm text-white/40">
                Opens after founding seats fill
              </div>
            )}
          </div>
        </div>

        {/* FAQ */}
        <section className="space-y-3">
          {[
            [
              "Is this investment advice?",
              "No. FinPilot is a research and education tool. Candidates are watch candidates with historical statistics — never buy/sell recommendations. Decisions and risk management are always yours.",
            ],
            [
              "Why should I trust the numbers?",
              "You shouldn't — you should check them. The scorecard is public, updated weekly, and includes the weeks we were wrong. That is the whole point.",
            ],
            [
              "How do I cancel?",
              "One click in Stripe, any time. And every purchase carries a 14-day unconditional refund.",
            ],
            [
              "Why is it priced this low?",
              "Early stage, honestly priced. Founding members lock this price forever; it will rise as the record and the product grow.",
            ],
          ].map(([q, a]) => (
            <details key={q} className="group rounded-xl border border-white/10 bg-white/[0.02] p-4">
              <summary className="cursor-pointer text-sm font-medium text-white/80 group-open:text-white">{q}</summary>
              <p className="mt-2 text-[13px] leading-relaxed text-white/60">{a}</p>
            </details>
          ))}
        </section>

        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-center">
          <p className="text-[13px] text-white/60">
            Not ready? The free brief stays genuinely useful — every morning, with the same open scorecard.
          </p>
          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-block text-sm font-medium text-sky-300 hover:text-sky-200"
          >
            Join the free daily brief →
          </a>
        </div>

        <footer className="flex items-start gap-2 pb-8 text-[11px] leading-relaxed text-white/35">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
          {DISCLAIMER}
        </footer>
      </div>
    </main>
  );
}
