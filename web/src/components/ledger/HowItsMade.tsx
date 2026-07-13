import { C } from "./_ledgerColors";

interface HowItsMadeProps {
  configSha?: string;
}

const COLUMNS = [
  {
    step: "01",
    title: "Scan",
    desc: "Every morning, before the market opens, the system reads over 1,800 US stocks — how each one is trading today compared to its own normal.",
  },
  {
    step: "02",
    title: "Grade",
    desc: "Three independent computer models look at the same stock and vote separately. When they agree, that agreement becomes the grade — A, B, or C.",
  },
  {
    step: "03",
    title: "Verify",
    desc: "Before anything is published, every rule is checked against days it has never seen before. Patterns that only worked by luck get thrown out.",
  },
  {
    step: "04",
    title: "Explain",
    desc: "Every grade comes with a plain-language reason, not just a ticker and a letter. You always know why a stock was picked — not just what it is.",
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
