"use client";

import { motion } from "framer-motion";
import { C } from "./_ledgerColors";

/**
 * "Fact-Checking Desk" — merged reskin of the old HeroGrid "Risk Shield"
 * metric cards + "Battle-Tested" backtest bars into one editorial block:
 * the newsroom's fact-checkers verifying every call before print.
 */
// Register (2026-07-14 web review): these are ILLUSTRATIVE research levels
// that show how the risk model reasons — not a stop/target recommendation.
const RISK_METRICS = [
  { label: "Illustrative stop", val: "$168.50", sub: "ATR-based" },
  { label: "Research target", val: "$198.00", sub: "R/R 1.8" },
  { label: "Illustrative size", val: "12%", sub: "Kelly-based" },
  { label: "Risk Score", val: "Low", sub: "0.3 / 1.0" },
];

const BACKTEST_METRICS = [
  { label: "Sharpe Ratio", val: "1.24", bar: 62 },
  { label: "Win Rate", val: "68%", bar: 68 },
  { label: "Max Drawdown", val: "12.4%", bar: 24 },
  { label: "Profit Factor", val: "2.1×", bar: 70 },
];

export default function FactCheckingDesk() {
  return (
    <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
      <div>
        <p className="mb-3 font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
          Risk Shield
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
          Illustrative levels — a research example of how the risk model reasons, not investment advice.
        </p>
      </div>

      <div>
        <p className="mb-3 font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.gold }}>
          Battle-Tested
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
