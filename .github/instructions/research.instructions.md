---
applyTo: "03-research/**"
description: Backtests, academic and GitHub evidence research
---

# Research Instructions

- Every claim about strategy performance must cite a specific
  backtest run, dataset, and date range. Never state a performance
  number without a traceable source.
- Never fabricate backtest results, Sharpe ratios, win rates, or any
  other metric. If a result is estimated or extrapolated, label it
  explicitly as "estimated, not backtested."
- Distinguish clearly between: (a) academic/theoretical evidence,
  (b) third-party GitHub implementations, (c) FinPilot's own backtests.
  Never blend these into a single unlabeled claim.
- If a research finding contradicts an existing product rule in
  `/01-product/*`, do not resolve the contradiction yourself — report
  it and let the Product layer own the resolution (per authority
  hierarchy, product rules only change via Level B/C process).
- Research conclusions that would change a live rule are **Level B**
  proposals, never direct edits to `/01-product/*`.
