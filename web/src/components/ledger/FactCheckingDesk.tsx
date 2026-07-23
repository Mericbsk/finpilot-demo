"use client";

import { motion } from "framer-motion";
import { C } from "./_ledgerColors";

/**
 * "Fact-Checking Desk" — merged reskin of the old risk and evidence panels
 * into one editorial block:
 * the newsroom's fact-checkers verifying every call before print.
 */
const RISK_METRICS = [
  { label: "Volatility range", val: "Elevated", sub: "ATR context" },
  { label: "Scenario band", val: "Wide", sub: "Historical range" },
  { label: "Exposure model", val: "Bounded", sub: "Portfolio rule" },
  { label: "Risk Score", val: "Low", sub: "0.3 / 1.0" },
];

const BACKTEST_METRICS = [
  { label: "Sample window", val: "2 years", bar: 62 },
  { label: "Live scorecard", val: "Pending", bar: 18 },
  { label: "Stress scenarios", val: "Reviewed", bar: 72 },
  { label: "Evidence status", val: "Research", bar: 54 },
];

export default function FactCheckingDesk() {
  return (
    <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
      <div>
        <p className="mb-3 font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
          Risk Model
        </p>
        <div className="grid grid-cols-2 gap-3">
          {RISK_METRICS.map((m, i) => (
            <motion.div
              key={m.label}
              initial={{ opacity: 0, scale: 0.92 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 + i * 0.06, duration: 0.35 }}
              className="border p-4 text-center"
              style={{ borderColor: C.rule }}
            >
              <div className="text-base font-bold" style={{ color: C.ink }}>{m.val}</div>
              <div className="mt-1 text-[10px]" style={{ color: C.inkSoft }}>{m.label}</div>
              <div className="text-[9px]" style={{ color: C.inkSoft }}>{m.sub}</div>
            </motion.div>
          ))}
        </div>
        <p className="mt-2 text-[9px] italic" style={{ color: C.inkSoft }}>
          Context for research review, not an instruction to trade. Decisions and risk remain yours.
        </p>
      </div>

      <div>
        <p className="mb-3 font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
          Evidence Desk
        </p>
        <div className="space-y-3">
          {BACKTEST_METRICS.map((m, i) => (
            <motion.div
              key={m.label}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 + i * 0.06, duration: 0.4 }}
              className="flex items-center gap-3"
            >
              <span className="w-28 shrink-0 text-[11px]" style={{ color: C.inkSoft }}>{m.label}</span>
              <div className="h-1.5 flex-1 overflow-hidden" style={{ background: C.paperDim }}>
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: `${m.bar}%` }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.4 + i * 0.08, duration: 0.8, ease: "easeOut" }}
                  className="h-full"
                  style={{ background: C.gold }}
                />
              </div>
              <span className="w-14 text-right text-xs font-semibold" style={{ color: C.ink }}>{m.val}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
