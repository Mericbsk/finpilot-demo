---
applyTo: "distribution/glossary.py,academy/**,web/src/app/academy/**"
description: Finance Academy, glossary, and user-facing documentation
---

# Content Instructions

Authority reference: `distribution/glossary.py` is the single source of
truth for glossary terminology (see `docs/INDEX.md` manifest id
`content-glossary`, status `active`). `web/public/dictionary.json` is
LEGACY — dashboard/finsense pages only, the landing page never reads it.
Academy lesson content is authored under `academy/` and exported to
`web/public/academy_lessons.json` (manifest id `academy-content`).

- Never define a financial or product term differently than it's
  defined in `scanner/`, `distribution/` (product) or `research/`,
  `reports/` (research). If a mismatch is found, flag it — do not
  silently pick one definition.
- Educational content (Finance Academy) must be accurate and
  evidence-based; never simplify a concept in a way that
  misrepresents risk or performance.
- New user-facing content that describes a product feature is
  **Level A** if it only documents an already-approved feature, but
  **Level B** if it implies a new feature, capability, or claim not
  yet approved elsewhere.
- Tone: clear, plain language, no marketing exaggeration, no
  unsupported performance claims (e.g., avoid "guaranteed returns"
  style language entirely — this is also a compliance concern).
- Keep glossary entries short, precise, and linked to their authority
  source file when the term originates from product or research docs.
