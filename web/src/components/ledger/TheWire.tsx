"use client";

import { motion } from "framer-motion";
import { C } from "./_ledgerColors";

/**
 * "The Wire" — reskin of the old HeroGrid `ScanTable` mockup. Presented as
 * the newsroom's raw incoming feed, ledger typography (mono ticker column).
 * NOTE: data below is illustrative/static, same as the original mockup —
 * see plan's "Değiştirilebilir bileşenler" note re: wiring to real
 * snapshot.candidates (deferred, needs separate approval).
 */
const ROWS = [
  { sym: "NVDA", score: 87, signal: "BUY", entry: "$179.00", sl: "$168.50", tp: "$198.00", rr: "1.8" },
  { sym: "META", score: 79, signal: "BUY", entry: "$634.60", sl: "$608.00", tp: "$682.00", rr: "1.8" },
  { sym: "AAPL", score: 74, signal: "BUY", entry: "$257.10", sl: "$245.80", tp: "$275.50", rr: "1.6" },
  { sym: "MSFT", score: 52, signal: "HOLD", entry: "—", sl: "—", tp: "—", rr: "—" },
  { sym: "TSLA", score: 38, signal: "SELL", entry: "$386.60", sl: "$405.00", tp: "$348.00", rr: "2.1" },
];

const SIGNAL_COLOR: Record<string, string> = { BUY: C.sage, HOLD: C.inkSoft, SELL: C.brick };

export default function TheWire() {
  return (
    <div className="border" style={{ borderColor: C.rule }}>
      <div
        className="grid grid-cols-7 gap-1 px-4 py-2.5 font-ledger-mono text-[9px] font-semibold uppercase tracking-[0.15em] border-b"
        style={{ color: C.inkSoft, borderColor: C.rule }}
      >
        <span>Symbol</span><span className="text-center">Score</span><span className="text-center">Signal</span>
        <span className="text-right">Entry</span><span className="text-right">Stop</span><span className="text-right">Target</span><span className="text-right">R/R</span>
      </div>
      {ROWS.map((r, i) => (
        <motion.div
          key={r.sym}
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 + i * 0.06, duration: 0.35 }}
          className="grid grid-cols-7 gap-1 px-4 py-2 text-[11px] border-b last:border-0"
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
          <span className="text-center font-bold" style={{ color: SIGNAL_COLOR[r.signal] }}>{r.signal}</span>
          <span className="text-right" style={{ color: C.inkSoft }}>{r.entry}</span>
          <span className="text-right" style={{ color: C.inkSoft }}>{r.sl}</span>
          <span className="text-right" style={{ color: C.inkSoft }}>{r.tp}</span>
          <span className="text-right font-medium" style={{ color: C.ink }}>{r.rr}</span>
        </motion.div>
      ))}
    </div>
  );
}
