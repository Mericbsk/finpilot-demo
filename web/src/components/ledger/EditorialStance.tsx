import { C } from "./_ledgerColors";

const CREDENTIALS = [
  "PPO Training",
  "HMM Regime Detection",
  "Ensemble Voting",
  "Kelly Sizing",
  "Monte Carlo Validation",
  "Telegram Alerts",
];

/** Editorial Stance band (between S6 and S7) — reskin of the old HeroGrid
 * "Differentiator" section: the masthead's editorial position + credentials. */
export default function EditorialStance() {
  return (
    <div className="border-y-2 py-14 text-center" style={{ borderColor: C.ink }}>
      <p className="mb-5 font-ledger-mono text-[10px] uppercase tracking-[0.25em]" style={{ color: C.gold }}>
        Our Editorial Stance
      </p>
      <h2 className="mx-auto max-w-3xl font-ledger-serif text-2xl font-bold leading-snug sm:text-3xl" style={{ color: C.ink }}>
        FinPilot doesn&apos;t wrap an LLM.
        <br />
        <span className="italic" style={{ color: C.inkSoft }}>
          It runs its own trained reinforcement learning models that learn from market data — not
          from prompts.
        </span>
      </h2>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {CREDENTIALS.map((tag) => (
          <span
            key={tag}
            className="border px-4 py-1.5 font-ledger-mono text-[11px] uppercase tracking-wide"
            style={{ borderColor: C.rule, color: C.inkSoft }}
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
