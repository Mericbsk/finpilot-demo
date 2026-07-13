"use client";

/**
 * FinPilot Web Demo — "yesterday's real brief, frozen".
 *
 * Reframed per Web Demo MVP Spec (2026-07-03):
 *  - Single Grade label (no BUY/SELL, no stop/TP, no position sizing)
 *  - Candidate cards: Grade + probability band + factor badges + rationale
 *  - Scorecard strip (the proof) + methodology note
 *  - Term cards (FinSense bridge), 3-question feedback, Telegram/waitlist CTAs
 *  - Data: static /demo_snapshot.json published daily by the distribution layer.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  MessageCircle,
  ScrollText,
  Send,
  ShieldQuestion,
  Sparkles,
} from "lucide-react";
import { BadgeWithTerm } from "@/components/TermCard";
import { apiFetch } from "@/lib/api";

/* Types mirror distribution/schema.py (demo view) */
interface Candidate {
  ticker: string;
  company?: string;
  grade: "A" | "B" | "C";
  prob_band: string;
  badges: string[];
  rationale: string;
  premium_only?: boolean;
}
interface Snapshot {
  schema: number;
  date: string;
  generated_at: string;
  universe: number;
  candidates: Candidate[];
  karne: {
    toplam_aday_bugun?: Record<string, number>;
    by_grade?: Record<string, { n?: number; hit_rate?: number | string }>;
    window?: string;
  } | null;
  warnings?: string[];
  sample?: boolean;
}

const TELEGRAM_URL = process.env.NEXT_PUBLIC_TELEGRAM_URL || "https://t.me/finpilot";
const DISCLAIMER =
  "FinPilot is a research and education tool; it does not provide investment advice. Past performance does not guarantee future results.";

const GRADE_STYLES: Record<string, { ring: string; chip: string; label: string }> = {
  A: { ring: "ring-[var(--ledger-sage)]", chip: "bg-[var(--ledger-sage)]/15 text-[var(--ledger-sage)]", label: "Rare, highest-conviction profile" },
  B: { ring: "ring-[var(--ledger-steel)]", chip: "bg-[var(--ledger-steel)]/15 text-[var(--ledger-steel)]", label: "Strong multi-factor profile" },
  C: { ring: "ring-[var(--ledger-rule)]", chip: "bg-[var(--ledger-ink-soft)]/15 text-[var(--ledger-ink-soft)]", label: "Watch-stage profile" },
};

function track(event: string) {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).plausible?.(event);
  } catch {
    /* noop */
  }
}

function CandidateCard({ c, onOpen }: { c: Candidate; onOpen: () => void }) {
  const s = GRADE_STYLES[c.grade] ?? GRADE_STYLES.C;
  return (
    <div className={`rounded-2xl border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-5 ring-1 ${s.ring}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-lg font-bold text-[var(--ledger-ink)]">
            ${c.ticker}
            {c.company ? <span className="ml-2 text-sm font-normal text-[var(--ledger-ink-soft)]">{c.company}</span> : null}
          </div>
          <div className="mt-1 text-[13px] text-[var(--ledger-ink-soft)]">
            Historically, candidates with this profile moved {"≥"}5% within 5 days about{" "}
            <span className="font-semibold text-[var(--ledger-ink)]">{c.prob_band}</span> of the time*
          </div>
        </div>
        <span className={`shrink-0 rounded-lg px-2.5 py-1 text-sm font-bold ${s.chip}`} title={s.label}>
          Grade {c.grade}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {c.badges.map((b) => (
          <BadgeWithTerm key={b} badge={b} />
        ))}
      </div>

      <p className="mt-3 text-[13px] leading-relaxed text-[var(--ledger-ink-soft)]">{c.rationale}</p>

      <button
        onClick={() => {
          track("demo-card-open");
          onOpen();
        }}
        className="mt-3 inline-flex items-center gap-1 text-[13px] font-medium text-[var(--ledger-ink)] hover:text-[var(--ledger-ink)]"
      >
        Why this grade? <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}

function Scorecard({ snap }: { snap: Snapshot }) {
  const totals = snap.karne?.toplam_aday_bugun ?? {};
  const byGrade = snap.karne?.by_grade ?? {};
  const totalToday = Object.values(totals).reduce((a, b) => a + (b || 0), 0);
  const shown = snap.candidates.length;

  return (
    <section id="karne" className="rounded-2xl border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-5">
      <div className="flex items-center gap-2 text-[var(--ledger-ink)]">
        <BarChart3 className="h-4 w-4 text-[var(--ledger-sage)]" />
        <h2 className="text-sm font-semibold">The open scorecard</h2>
      </div>

      {totalToday > 0 && (
        <p className="mt-2 text-[13px] text-[var(--ledger-ink-soft)]">
          On {snap.date} the system flagged <span className="font-semibold text-[var(--ledger-ink)]">{totalToday} candidates</span>{" "}
          ({Object.entries(totals).map(([g, n]) => `${n}× Grade ${g}`).join(", ")}). You are seeing{" "}
          <span className="font-semibold text-[var(--ledger-ink)]">{shown}</span> of them here — the full daily list is part of the
          premium brief.
        </p>
      )}

      {Object.keys(byGrade).length > 0 ? (
        <div className="mt-3 grid grid-cols-3 gap-2">
          {(["A", "B", "C"] as const).map((g) => {
            const st = byGrade[g];
            if (!st) return <div key={g} />;
            return (
              <div key={g} className="rounded-xl bg-[var(--ledger-paper-dim)] p-3 text-center">
                <div className="text-xs text-[var(--ledger-ink-soft)]">Grade {g}</div>
                <div className="text-lg font-bold text-[var(--ledger-ink)]">
                  {typeof st.hit_rate === "number" ? `${Math.round(st.hit_rate * 100)}%` : st.hit_rate ?? "—"}
                </div>
                <div className="text-[10px] text-[var(--ledger-ink-soft)]">n={st.n ?? "—"}</div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="mt-3 text-[12px] text-[var(--ledger-ink-soft)]">
          Grade-level hit rates are published as the sample builds — including the bad weeks. Grade A is rare (~1/day),
          so its statistics accumulate slowly. That honesty is the product.
        </p>
      )}

      <p className="mt-3 text-[11px] text-[var(--ledger-ink-soft)]">
        *Measured as a {"≥"}5% absolute move within 5 trading days, against the day&apos;s base rate — a research
        target, not a profit claim. Costs, slippage and timing are not included.
      </p>
    </section>
  );
}

function DetailModal({ c, onClose }: { c: Candidate; onClose: () => void }) {
  const s = GRADE_STYLES[c.grade] ?? GRADE_STYLES.C;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-[var(--ledger-rule)] bg-[var(--ledger-paper)] p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <div className="text-xl font-bold text-[var(--ledger-ink)]">${c.ticker}</div>
          <span className={`rounded-lg px-2.5 py-1 text-sm font-bold ${s.chip}`}>Grade {c.grade}</span>
        </div>
        <p className="mt-1 text-[12px] text-[var(--ledger-ink-soft)]">{s.label}</p>

        <h3 className="mt-4 text-sm font-semibold text-[var(--ledger-ink)]">Why it was flagged</h3>
        <p className="mt-1 text-[13px] leading-relaxed text-[var(--ledger-ink-soft)]">{c.rationale}</p>

        <h3 className="mt-4 text-sm font-semibold text-[var(--ledger-ink)]">Aligned factors</h3>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {c.badges.map((b) => (
            <BadgeWithTerm key={b} badge={b} />
          ))}
        </div>

        <div className="mt-5 rounded-xl bg-[var(--ledger-paper-dim)] p-4">
          <p className="text-[13px] text-[var(--ledger-ink-soft)]">
            What happened in the 5 days after this snapshot? Today&apos;s brief — and the follow-up on every past
            candidate — goes out on Telegram each morning at 08:30.
          </p>
          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => track("demo-modal-telegram")}
            className="mt-3 inline-flex items-center gap-2 rounded-lg bg-[var(--ledger-gold)]/20 px-3 py-2 text-sm font-medium text-[var(--ledger-gold)] hover:bg-[var(--ledger-gold)]/30"
          >
            <Send className="h-4 w-4" /> Get today&apos;s brief
          </a>
        </div>

        <p className="mt-4 text-[11px] text-[var(--ledger-ink-soft)]">{DISCLAIMER}</p>
        <button onClick={onClose} className="mt-4 text-sm text-[var(--ledger-ink-soft)] hover:text-[var(--ledger-ink)]">
          Close
        </button>
      </div>
    </div>
  );
}

function FeedbackForm() {
  const [q1, setQ1] = useState("");
  const [q2, setQ2] = useState("");
  const [q3, setQ3] = useState("");
  const [q3Why, setQ3Why] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");

  const submit = async () => {
    if (!(q1 || q2 || q3)) return;
    setState("sending");
    try {
      const res = await apiFetch("/api/v1/demo/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: Math.random().toString(36).slice(2, 10),
          q1,
          q2,
          q3,
          q3_why: q3Why,
          source: "demo",
        }),
      });
      setState(res.ok ? "done" : "error");
      if (res.ok) track("demo-feedback-submit");
    } catch {
      setState("error");
    }
  };

  if (state === "done") {
    return (
      <div className="rounded-2xl border border-[var(--ledger-sage)]/40 bg-[var(--ledger-sage)]/5 p-5 text-center">
        <CheckCircle2 className="mx-auto h-6 w-6 text-[var(--ledger-sage)]" />
        <p className="mt-2 text-sm text-[var(--ledger-ink)]">Thank you — every answer is read, every Friday.</p>
        <a
          href={TELEGRAM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-[var(--ledger-gold)] hover:opacity-80"
        >
          <Send className="h-4 w-4" /> Join the daily brief on Telegram
        </a>
      </div>
    );
  }

  return (
    <section className="rounded-2xl border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-5">
      <div className="flex items-center gap-2 text-[var(--ledger-ink)]">
        <MessageCircle className="h-4 w-4 text-[var(--ledger-ink)]" />
        <h2 className="text-sm font-semibold">60 seconds of feedback shapes this product</h2>
      </div>
      <div className="mt-3 space-y-3">
        <label className="block text-[13px] text-[var(--ledger-ink-soft)]">
          In your own words — what does this product do?
          <textarea
            value={q1}
            onChange={(e) => setQ1(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-lg border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-2 text-sm text-[var(--ledger-ink)] outline-none focus:border-[var(--ledger-ink)]"
          />
        </label>
        <label className="block text-[13px] text-[var(--ledger-ink-soft)]">
          Most useful thing — and most confusing thing?
          <textarea
            value={q2}
            onChange={(e) => setQ2(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-lg border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-2 text-sm text-[var(--ledger-ink)] outline-none focus:border-[var(--ledger-ink)]"
          />
        </label>
        <div className="text-[13px] text-[var(--ledger-ink-soft)]">
          Would you pay {"€"}9/month for the full daily version?
          <div className="mt-1 flex gap-2">
            {(["yes", "maybe", "no"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setQ3(v)}
                className={`rounded-lg px-3 py-1.5 text-sm capitalize ${
                  q3 === v ? "bg-[var(--ledger-ink)]/20 text-[var(--ledger-ink)]" : "bg-[var(--ledger-paper-dim)] text-[var(--ledger-ink-soft)] hover:bg-[var(--ledger-rule)]"
                }`}
              >
                {v}
              </button>
            ))}
          </div>
          {q3 && (
            <input
              value={q3Why}
              onChange={(e) => setQ3Why(e.target.value)}
              placeholder="why? (optional)"
              className="mt-2 w-full rounded-lg border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-2 text-sm text-[var(--ledger-ink)] outline-none focus:border-[var(--ledger-ink)]"
            />
          )}
        </div>
        <button
          onClick={submit}
          disabled={state === "sending"}
          className="rounded-lg bg-[var(--ledger-ink)] px-4 py-2 text-sm font-medium text-[var(--ledger-paper)] hover:opacity-90 disabled:opacity-50"
        >
          {state === "sending" ? "Sending…" : "Send"}
        </button>
        {state === "error" && (
          <p className="text-[12px] text-[var(--ledger-brick)]">Could not send right now — please try again later.</p>
        )}
      </div>
    </section>
  );
}

export default function DemoPage() {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ok" | "missing">("loading");
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  useEffect(() => {
    track("demo-start");
    fetch("/demo_snapshot.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("missing"))))
      .then((d: Snapshot) => {
        setSnap(d);
        setLoadState("ok");
      })
      .catch(() => setLoadState("missing"));
  }, []);

  const visible = useMemo(() => (snap?.candidates ?? []).filter((c) => !c.premium_only), [snap]);

  return (
    <main className="ledger min-h-screen bg-[var(--ledger-paper)] px-4 py-8">
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <Link href="/" className="inline-flex items-center gap-1 text-sm text-[var(--ledger-ink-soft)] hover:text-[var(--ledger-ink)]">
            <ArrowLeft className="h-4 w-4" /> finpilot.at
          </Link>
          <h1 className="mt-3 text-2xl font-bold text-[var(--ledger-ink)]">
            Yesterday&apos;s brief — <span className="text-[var(--ledger-sage)]">real, dated, frozen</span>
          </h1>
          <p className="mt-2 text-[14px] leading-relaxed text-[var(--ledger-ink-soft)]">
            This is not a mockup. Below is the actual output of the morning scan
            {snap ? (
              <>
                {" "}
                from <span className="font-semibold text-[var(--ledger-ink)]">{snap.date}</span> across{" "}
                <span className="font-semibold text-[var(--ledger-ink)]">{snap.universe.toLocaleString()} stocks</span>
              </>
            ) : null}
            . Today&apos;s edition goes out on Telegram at 08:30 — we publish yesterday&apos;s here so you can judge us
            with hindsight.
          </p>
          <div className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-[var(--ledger-rule)] px-2.5 py-1 text-[11px] text-[var(--ledger-ink-soft)]">
            <CalendarDays className="h-3 w-3" /> snapshot: {snap?.date ?? "…"}
            {snap?.sample ? " · sample data until first live publish" : ""}
          </div>
        </div>

        {loadState === "loading" && (
          <div className="rounded-2xl border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-8 text-center text-[var(--ledger-ink-soft)]">
            Loading yesterday&apos;s brief…
          </div>
        )}
        {loadState === "missing" && (
          <div className="rounded-2xl border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-8 text-center">
            <ShieldQuestion className="mx-auto h-6 w-6 text-[var(--ledger-ink-soft)]" />
            <p className="mt-2 text-sm text-[var(--ledger-ink-soft)]">
              No snapshot published yet (markets may be closed). The daily brief resumes on the next trading day.
            </p>
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-[var(--ledger-gold)] hover:opacity-80"
            >
              <Send className="h-4 w-4" /> Get notified on Telegram
            </a>
          </div>
        )}
        {loadState === "ok" && snap && (
          <>
            <div className="space-y-4">
              {visible.map((c, i) => (
                <CandidateCard key={c.ticker} c={c} onOpen={() => setOpenIdx(i)} />
              ))}
              {visible.length === 0 && (
                <div className="rounded-2xl border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-6 text-center text-sm text-[var(--ledger-ink-soft)]">
                  No candidates cleared the bar on {snap.date}. Some days the best candidate is patience — and we say
                  so instead of inventing one.
                </div>
              )}
            </div>

            <Scorecard snap={snap} />
          </>
        )}

        <section className="rounded-2xl border border-[var(--ledger-rule)] bg-[var(--ledger-paper-dim)] p-5">
          <div className="flex items-center gap-2 text-[var(--ledger-ink)]">
            <ScrollText className="h-4 w-4 text-[var(--ledger-gold)]" />
            <h2 className="text-sm font-semibold">How the grade is made</h2>
          </div>
          <ol className="mt-3 space-y-2 text-[13px] text-[var(--ledger-ink-soft)]">
            <li>1 · Every morning 1,800+ US stocks are scanned for volume, volatility, short-interest and catalyst patterns.</li>
            <li>2 · Independent factors combine into a calibrated probability — checked weekly against reality.</li>
            <li>3 · Candidates get a single Grade (A/B/C). Grade A is rare by design (~1/day).</li>
            <li>4 · Every outcome is recorded and published in the open scorecard — including the misses.</li>
          </ol>
        </section>

        <section className="grid gap-3 sm:grid-cols-2">
          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => track("demo-cta-telegram")}
            className="flex items-center justify-between rounded-2xl border border-[var(--ledger-gold)]/40 bg-[var(--ledger-gold)]/10 p-4 hover:bg-[var(--ledger-gold)]/15"
          >
            <div>
              <div className="text-sm font-semibold text-[var(--ledger-ink)]">Today&apos;s brief, every morning</div>
              <div className="text-[12px] text-[var(--ledger-ink-soft)]">08:30 · one message a day · free</div>
            </div>
            <Send className="h-5 w-5 text-[var(--ledger-gold)]" />
          </a>
          <Link
            href="/#waitlist"
            onClick={() => track("demo-cta-waitlist")}
            className="flex items-center justify-between rounded-2xl border border-[var(--ledger-ink)]/20 bg-[var(--ledger-ink)]/5 p-4 hover:bg-[var(--ledger-ink)]/10"
          >
            <div>
              <div className="text-sm font-semibold text-[var(--ledger-ink)]">Full dashboard (invite beta)</div>
              <div className="text-[12px] text-[var(--ledger-ink-soft)]">watchlists, alerts, full history</div>
            </div>
            <Sparkles className="h-5 w-5 text-[var(--ledger-ink)]" />
          </Link>
        </section>

        <FeedbackForm />

        <footer className="pb-8 pt-2 text-center text-[11px] leading-relaxed text-[var(--ledger-ink-soft)]">{DISCLAIMER}</footer>
      </div>

      {openIdx !== null && visible[openIdx] && <DetailModal c={visible[openIdx]} onClose={() => setOpenIdx(null)} />}
    </main>
  );
}
