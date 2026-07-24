---
applyTo: "01-product/**"
description: Product rules — scanner, composite score, entry/exit logic
---

# Product Instructions

Authority reference: `/01-product/composite-score.md` and
`/01-product/entry-exit-rules.md` — these are the single source of
truth for their respective concepts. Do not restate their formulas
elsewhere; link to them.

- Any change to the composite score formula, scanner filters, or
  entry/exit thresholds is **Level B** at minimum. If it changes risk
  exposure (position sizing, stop-loss logic), it escalates to
  **Level C**.
- Before modifying a rule, check whether it is referenced by
  `/02-engineering/*` (implementation) or `/03-research/*` (backtest
  evidence) — flag those files as needing review if the rule changes.
- Never introduce a new scoring dimension or filter without stating
  the backtest or research evidence behind it. If no evidence exists,
  label the proposal as "hypothesis, unvalidated."
- Terminology used here must match `/04-content/glossary.md` exactly.
  If a new term is introduced, flag it for addition to the glossary.
- Do not describe UI/UX behavior here — that belongs in
  `/02-engineering/*` or a dedicated design file.
