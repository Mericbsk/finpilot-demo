import { C } from "./_ledgerColors";

interface HowItsMadeProps {
  configSha?: string;
}

const COLUMNS = [
  {
    step: "01",
    title: "Scan",
    desc: "Every session, the scanner reads 1,800+ symbols across volume, gap, RVOL, ATR, and technical structure — the raw wire feed of the market.",
  },
  {
    step: "02",
    title: "Grade",
    desc: "Three specialised DRL agents — Trend, Range, and Volatility — vote independently. No single model decides; a research grade (A/B/C) is the consensus, not a guess.",
  },
  {
    step: "03",
    title: "Verify",
    desc: "Walk-forward optimisation and out-of-sample testing before anything is printed. If a rule doesn't survive data it wasn't tuned on, it doesn't ship.",
  },
  {
    step: "04",
    title: "Teach",
    desc: "Every grade carries its reasoning in plain language — the badge, the risk note, the calibration promise. You learn the 'why', not just the ticker.",
  },
];

/** S5 "How It's Made" — 4-column editorial process, replacing the old
 * 3-step (Scan/Analyze/Decide) marketing copy with a more honest pipeline. */
export default function HowItsMade({ configSha }: HowItsMadeProps) {
  return (
    <div id="how-its-made">
      <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
        {COLUMNS.map((c) => (
          <div key={c.step} className="border-t-2 pt-4" style={{ borderColor: C.ink }}>
            <span className="font-ledger-mono text-xs" style={{ color: C.gold }}>
              {c.step}
            </span>
            <h3 className="mt-1 font-ledger-serif text-xl font-bold" style={{ color: C.ink }}>
              {c.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: C.inkSoft }}>
              {c.desc}
            </p>
          </div>
        ))}
      </div>
      {configSha && (
        <p className="mt-8 text-center font-ledger-mono text-[10px] uppercase tracking-widest" style={{ color: C.inkSoft }}>
          Print run · config {configSha}
        </p>
      )}
    </div>
  );
}
