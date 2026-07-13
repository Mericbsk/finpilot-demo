/**
 * JS-side mirror of the CSS custom properties defined in globals.css
 * (`--ledger-*`). Used where inline `style={{ background: C.gold }}` is more
 * convenient than a Tailwind arbitrary-value class. Keep in sync with
 * globals.css if the palette changes (placeholder values pending
 * design_ref/*.dc.html).
 */
export const C = {
  paper: "var(--ledger-paper)",
  paperDim: "var(--ledger-paper-dim)",
  ink: "var(--ledger-ink)",
  inkSoft: "var(--ledger-ink-soft)",
  rule: "var(--ledger-rule)",
  gold: "var(--ledger-gold)",
  sage: "var(--ledger-sage)",
  brick: "var(--ledger-brick)",
  steel: "var(--ledger-steel)",
  amberLive: "var(--ledger-amber-live)",
} as const;
