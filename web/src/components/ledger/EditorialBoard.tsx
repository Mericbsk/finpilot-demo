"use client";

import { motion } from "framer-motion";
import { C } from "./_ledgerColors";

/**
 * "The Editorial Board" — reskin of the old HeroGrid `EnsembleVoting` mockup.
 * Framed as three editors voting on tomorrow's front page instead of three
 * DRL agents voting on a trade — same underlying idea (independent votes,
 * weighted consensus), ledger voice.
 */
// Register (2026-07-14 web review): each editor gives a READING, not a
// BUY/HOLD vote. The consensus is a combined GRADE, not a "BUY". No advice
// language on the public page.
const AGENTS = [
  { name: "Trend Editor", read: "strong", conf: 92, color: C.sage },
  { name: "Range Editor", read: "neutral", conf: 61, color: C.inkSoft },
  { name: "Volatility Editor", read: "elevated", conf: 74, color: C.sage },
];

export default function EditorialBoard() {
  return (
    <div className="space-y-2.5">
      {AGENTS.map((a, i) => (
        <motion.div
          key={a.name}
          initial={{ opacity: 0, x: 14 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 + i * 0.08, duration: 0.35 }}
          className="flex items-center gap-3 border px-4 py-3"
          style={{ borderColor: C.rule }}
        >
          <div className="h-2 w-2 shrink-0 rounded-full" style={{ background: a.color }} />
          <span className="w-32 text-xs font-semibold" style={{ color: C.ink }}>{a.name}</span>
          <div className="h-1 flex-1 overflow-hidden rounded-none" style={{ background: C.paperDim }}>
            <motion.div
              initial={{ width: 0 }}
              whileInView={{ width: `${a.conf}%` }}
              viewport={{ once: true }}
              transition={{ delay: 0.4 + i * 0.1, duration: 0.7 }}
              className="h-full"
              style={{ background: a.color }}
            />
          </div>
          <span className="w-8 text-right text-[10px]" style={{ color: C.inkSoft }}>{a.conf}%</span>
          <span className="w-16 text-right text-[10px] font-bold" style={{ color: a.color }}>{a.read}</span>
        </motion.div>
      ))}
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.5, duration: 0.4 }}
        className="flex items-center justify-between border-2 px-4 py-2.5"
        style={{ borderColor: C.sage }}
      >
        <span className="text-xs font-bold" style={{ color: C.sage }}>Combined read: Grade B</span>
        <span className="text-[10px]" style={{ color: C.sage }}>88% factor agreement</span>
      </motion.div>
    </div>
  );
}
