"use client";

import { motion } from "framer-motion";
import { C } from "./_ledgerColors";

/**
 * "The Wire" — the newsroom's raw incoming feed, ledger typography.
 *
 * Register (2026-07-14 web review): this is a RESEARCH GRADE feed, not a
 * trade blotter. It shows a letter grade + a plain-language reason — never
 * BUY/SELL, entry/stop/target, or R/R. Those price levels live only on the
 * logged-in dashboard (with disclaimers + user context), never on the public
 * marketing page. Data below is illustrative/static, same as the original
 * mockup — see plan re: wiring to real snapshot.candidates (deferred).
 */
const ROWS = [
  { sym: "NVDA", score: 87, grade: "B", why: "volume and momentum point the same way" },
  { sym: "META", score: 79, grade: "B", why: "broad participation, not a few stray orders" },
  { sym: "AAPL", score: 74, grade: "B", why: "trend and volume agree" },
  { sym: "MSFT", score: 52, grade: "—", why: "signals are mixed — no clear read" },
  { sym: "TSLA", score: 38, grade: "C", why: "weak setup — not a watch candidate" },
];

const GRADE_COLOR: Record<string, string> = { A: C.sage, B: C.sage, "—": C.inkSoft, C: C.brick };

export default function TheWire() {
  return (
    <div>
      <div className="border" style={{ borderColor: C.rule }}>
        <div
          className="grid grid-cols-[64px_52px_56px_1fr] gap-2 px-4 py-2.5 font-ledger-mono text-[9px] font-semibold uppercase tracking-[0.15em] border-b"
          style={{ color: C.inkSoft, borderColor: C.rule }}
        >
          <span>Symbol</span>
          <span className="text-center">Score</span>
          <span className="text-center">Grade</span>
          <span>Why it stood out</span>
        </div>
        {ROWS.map((r, i) => (
          <motion.div
            key={r.sym}
            initial={{ opacity: 0, x: -10 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.15 + i * 0.06, duration: 0.35 }}
            className="grid grid-cols-[64px_52px_56px_1fr] items-center gap-2 px-4 py-2 text-[11px] border-b last:border-0"
            style={{ borderColor: C.rule }}
          >
            <span className="font-ledger-mono font-semibold" style={{ color: C.ink }}>{r.sym}</span>
            <span className="text-center">
              <span
                className="inline-block min-w-[28px] px-2 py-0.5 font-ledger-mono text-[10px] font-medium"
                style={{ background: C.paperDim, color: C.ink }}
              >
                {r.score}
              </span>
            </span>
            <span className="text-center font-bold" style={{ color: GRADE_COLOR[r.grade] }}>{r.grade}</span>
            <span style={{ color: C.inkSoft }}>{r.why}</span>
          </motion.div>
        ))}
      </div>
      <p className="mt-2 text-[10px] italic" style={{ color: C.inkSoft }}>
        Grades are a research read, not buy/sell advice. Every decision and its risk are yours.
      </p>
    </div>
  );
}
