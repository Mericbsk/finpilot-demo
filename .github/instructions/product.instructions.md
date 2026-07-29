---
applyTo: "scanner/**,distribution/**"
description: Product rules — scanner, composite score, entry/exit logic
---

# Product Instructions

Authority reference: **GAP** — no standalone `composite-score.md` or
`entry-exit-rules.md` exists (see `docs/INDEX.md` manifest id
`product-rules`, status `gap`). The rule currently lives only in code
(`scanner/`, `distribution/`) and in `YONERGE.md` §2's scanner↔distribution
contract fields. Do not restate formulas from memory; read the code and
`YONERGE.md` §2 directly.

- Any change to the composite score formula, scanner filters, or
  entry/exit thresholds is **Level B** at minimum. If it changes risk
  exposure (position sizing, stop-loss logic), it escalates to
  **Level C**.
- Before modifying a rule, check whether it is referenced by
  `api/`, `core/`, `web/src/` (implementation) or `research/`, `reports/`
  (backtest evidence) — flag those files as needing review if the rule
  changes.
- Never introduce a new scoring dimension or filter without stating
  the backtest or research evidence behind it. If no evidence exists,
  label the proposal as "hypothesis, unvalidated."
- Terminology used here must match `distribution/glossary.py` exactly.
  If a new term is introduced, flag it for addition to the glossary.
- Do not describe UI/UX behavior here — that belongs in
  `api/`, `core/`, `web/src/` or a dedicated design file.
