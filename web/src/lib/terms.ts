/**
 * Core glossary terms for contextual ⓘ cards (Demo Spec §3 / FinSense bridge).
 * Static v1 — will be fed from the FinSense content pack later.
 */

export interface Term {
  slug: string;
  name: string;
  short: string; // ≤60 words, plain language
}

export const TERMS: Record<string, Term> = {
  squeeze: {
    slug: "short-squeeze",
    name: "Short Squeeze",
    short:
      "When many traders have bet against a stock (short selling) and the price rises, they may be forced to buy back shares to limit losses — which pushes the price up even faster. High short interest + a price gap is the classic ignition setup.",
  },
  "short-interest": {
    slug: "short-interest",
    name: "Short Interest",
    short:
      "The share of a company's stock that has been sold short. A high value means many are betting on a decline — and also that sharp upward moves can accelerate as shorts cover.",
  },
  gap: {
    slug: "gap",
    name: "Price Gap",
    short:
      "When a stock opens notably higher or lower than yesterday's close. Gaps usually signal overnight news or strong order flow and often set the tone for the session.",
  },
  rvol: {
    slug: "rvol",
    name: "Relative Volume (RVOL)",
    short:
      "Today's trading volume compared to what is normal for this stock. RVOL above ~1.5 means unusual interest — something is happening.",
  },
  volume: {
    slug: "volume-spike",
    name: "Volume Spike",
    short:
      "A sudden jump in shares traded. Confirms that a price move is backed by real participation rather than thin drift.",
  },
  momentum: {
    slug: "momentum",
    name: "Momentum",
    short:
      "The tendency of recent price strength to persist over short horizons. Momentum in a calm (low-volatility) tape is historically more reliable than momentum driven by chaos.",
  },
  contraction: {
    slug: "contraction",
    name: "Range Contraction",
    short:
      "A period of unusually narrow price range. Like a coiled spring, contraction often precedes expansion — the scanner watches for the transition.",
  },
  regime: {
    slug: "market-regime",
    name: "Market Regime",
    short:
      "The market's overall mode — trending or range-bound, risk-on or risk-off. The same signal behaves differently in different regimes, so grading accounts for it.",
  },
  early_tier: {
    slug: "early-tier",
    name: "Early-Detection Ladder",
    short:
      "FinPilot tracks setups through WATCH → SETUP → TRIGGER → CONFIRM stages. Higher rungs mean more conditions have aligned — fewer, but better-qualified candidates.",
  },
  catalyst: {
    slug: "catalyst",
    name: "Catalyst",
    short:
      "A concrete event that can move a price: earnings, an FDA decision, an 8-K filing, a major contract. Candidates with a real catalyst behave differently from quiet drifters.",
  },
  grade: {
    slug: "grade",
    name: "Grade (A/B/C)",
    short:
      "FinPilot's single quality label. It combines a calibrated probability with how many independent factors align. Grade A is rare (~1/day) and historically hit large moves most often. It is a research grade — not a buy recommendation.",
  },
  calibration: {
    slug: "calibration",
    name: "Calibration",
    short:
      "A probability is calibrated when it matches reality: of all candidates we mark '~60%', about 60% should actually move. FinPilot publishes its scorecard so you can check this yourself.",
  },
  "base-rate": {
    slug: "base-rate",
    name: "Base Rate",
    short:
      "How often an event happens with no filtering at all. Any signal must be judged against this baseline — that is exactly what the scorecard's 'lift' measures.",
  },
  liquidity: {
    slug: "liquidity",
    name: "Liquidity",
    short:
      "How easily a stock trades without moving its own price. Low liquidity means wide spreads and slippage — a key hidden cost in small caps.",
  },
};

export function termForBadge(badge: string): Term | undefined {
  return TERMS[badge];
}
