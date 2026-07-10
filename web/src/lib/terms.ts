/**
 * AUTO-GENERATED from distribution/glossary.py — DO NOT EDIT BY HAND.
 * Regenerate with:  python scripts/gen_terms_ts.py
 * Single source of truth for glossary content (E4).
 */

export interface Term {
  slug: string;
  name: string;
  short: string; // plain language, ≤60 words
}

export const TERMS: Record<string, Term> = {
  "squeeze": {
    slug: "short-squeeze",
    name: "Short Squeeze",
    short:
      "When many traders have bet against a stock (short selling) and the price rises, they may be forced to buy back shares to limit losses — which pushes the price up even faster. High short interest plus a price gap is the classic ignition setup.",
  },
  "short-interest": {
    slug: "short-interest",
    name: "Short Interest",
    short:
      "The share of a company's stock that has been sold short. A high value means many are betting on a decline — and also that sharp upward moves can accelerate as shorts cover.",
  },
  "catalyst": {
    slug: "catalyst",
    name: "Catalyst",
    short:
      "A concrete event that can move a price: earnings, an FDA decision, an 8-K filing, a major contract. Candidates with a real catalyst behave differently from quiet drifters.",
  },
  "rvol": {
    slug: "rvol",
    name: "Relative Volume (RVOL)",
    short:
      "Today's trading volume compared to what is normal for this stock. RVOL above ~1.5 means unusual interest — something is happening.",
  },
  "gap": {
    slug: "gap",
    name: "Price Gap",
    short:
      "When a stock opens notably higher or lower than yesterday's close. Gaps usually signal overnight news or strong order flow and often set the tone for the session.",
  },
  "momentum": {
    slug: "momentum",
    name: "Momentum",
    short:
      "The tendency of recent price strength to persist over short horizons. Momentum in a calm (low-volatility) tape is historically more reliable than momentum driven by chaos.",
  },
  "volume": {
    slug: "volume-spike",
    name: "Volume Spike",
    short:
      "A sudden jump in shares traded. Confirms that a price move is backed by real participation rather than thin drift.",
  },
  "contraction": {
    slug: "range-contraction",
    name: "Range Contraction",
    short:
      "A period of unusually narrow price range. Like a coiled spring, contraction often precedes expansion — the scanner watches for the transition.",
  },
  "regime": {
    slug: "market-regime",
    name: "Market Regime",
    short:
      "The market's overall mode — trending or range-bound, risk-on or risk-off. The same signal behaves differently in different regimes, so grading accounts for it.",
  },
  "early_tier": {
    slug: "early-tier",
    name: "Early-Detection Ladder",
    short:
      "FinPilot tracks setups through WATCH → SETUP → TRIGGER → CONFIRM stages. Higher rungs mean more conditions have aligned — fewer, but better-qualified candidates.",
  },
  "grade": {
    slug: "grade",
    name: "Grade (A/B/C)",
    short:
      "FinPilot's single quality label. It combines a calibrated probability with how many independent factors align. Grade A is rare (~1/day) and historically hit large moves most often. It is a research grade — not a recommendation.",
  },
  "calibration": {
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
  "lift": {
    slug: "lift",
    name: "Lift",
    short:
      "A signal's hit rate divided by the base rate. Lift above 1 means the filter genuinely improves on random selection; lift near 1 means it only mirrors the market.",
  },
  "out-of-sample": {
    slug: "out-of-sample",
    name: "Out-of-Sample Test",
    short:
      "Testing a rule on data it was not tuned on. In-sample results flatter; out-of-sample results tell the truth. FinPilot promotes factors only after they survive this exam.",
  },
  "walk-forward": {
    slug: "walk-forward",
    name: "Walk-Forward Validation",
    short:
      "A validation method that trains on one period and tests on the next, rolling forward through history — the closest a backtest gets to how live trading actually unfolds.",
  },
  "survivorship-bias": {
    slug: "survivorship-bias",
    name: "Survivorship Bias",
    short:
      "The error of studying only what survived to today. Delisted or failed stocks vanish from datasets, silently inflating historical results. Honest research accounts for the fallen.",
  },
  "risk-reward": {
    slug: "risk-reward",
    name: "Risk/Reward Ratio",
    short:
      "The ratio of potential gain to potential loss on a setup. A high ratio is attractive only if the probability of the good outcome is realistic — ratio and probability must be read together.",
  },
  "atr": {
    slug: "atr",
    name: "ATR (Average True Range)",
    short:
      "The stock's typical daily movement width. High ATR means the price travels far in a normal day — more opportunity and more risk, in equal measure.",
  },
  "liquidity": {
    slug: "liquidity",
    name: "Liquidity",
    short:
      "How easily a stock trades without moving its own price. Low liquidity means wide spreads and slippage — a key hidden cost in small caps.",
  },
  "spread": {
    slug: "bid-ask-spread",
    name: "Bid-Ask Spread",
    short:
      "The gap between the highest buyer and the lowest seller. It is a real cost paid on every round trip — small on liquid large caps, punishing on thin small caps.",
  },
  "float": {
    slug: "float",
    name: "Float",
    short:
      "The number of shares actually available for trading (excluding insiders and locked holdings). A small float means the same buying pressure produces a much sharper move.",
  },
  "market-cap": {
    slug: "market-cap",
    name: "Market Capitalization",
    short:
      "Share price multiplied by total shares. Size class shapes behaviour: mega-caps grind, small caps jump. FinPilot's hunting ground is mostly the jumpy end.",
  },
  "halt": {
    slug: "trading-halt",
    name: "Trading Halt",
    short:
      "A temporary exchange pause, usually for pending news or extreme volatility. Positions cannot be exited during a halt, and the reopening price can land far from the last print.",
  },
  "offering": {
    slug: "offering-dilution",
    name: "Offering & Dilution",
    short:
      "When a company raises cash by selling new shares, each existing share owns a smaller slice — dilution. Speculative small caps fund themselves this way; an S-1 or 424B filing is the tell.",
  },
  "earnings-drift": {
    slug: "earnings-drift",
    name: "Post-Earnings Drift (PEAD)",
    short:
      "After a genuine earnings surprise, prices often keep drifting in the surprise's direction for days or weeks — one of the most persistent documented market patterns.",
  },
  "sector-rotation": {
    slug: "sector-rotation",
    name: "Sector Rotation",
    short:
      "Capital cycles between sectors as conditions shift. Recognising which group money is entering — and leaving — explains why identical setups work in one month and fail the next.",
  },
  "breakout": {
    slug: "breakout",
    name: "Breakout",
    short:
      "Price clearing a level it failed at repeatedly, ideally on strong volume. Volume is the credibility test — a quiet breakout is often just noise wearing a costume.",
  },
  "false-breakout": {
    slug: "false-breakout",
    name: "False Breakout",
    short:
      "Price pokes above a key level, attracts buyers, then snaps back below — trapping them. Frequent in thin stocks; confirmation (a close beyond, with volume) filters many of them.",
  },
  "fomo": {
    slug: "fomo",
    name: "FOMO",
    short:
      "Fear of missing out pushes traders to chase moves already well underway — typically entering at the most expensive point, without a plan. The scorecard's cure: most days offer another candidate tomorrow.",
  },
  "overtrading": {
    slug: "overtrading",
    name: "Overtrading",
    short:
      "Trading more often than your edge justifies. Each extra trade adds spread, slippage and decision fatigue — the quiet killer of otherwise decent strategies.",
  },
  "drawdown": {
    slug: "drawdown",
    name: "Drawdown",
    short:
      "The decline from a peak to the following trough. Deep drawdowns are hard to recover from mathematically — a 50% loss needs a 100% gain — which is why risk discipline exists.",
  },
  "position-sizing": {
    slug: "position-sizing",
    name: "Position Sizing",
    short:
      "Deciding how much of your capital a single idea deserves. Sizing — not entry timing — is what usually separates accounts that survive from accounts that don't.",
  },
};

export function termForBadge(badge: string): Term | undefined {
  return TERMS[badge];
}
