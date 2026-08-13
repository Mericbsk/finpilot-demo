# Mirror Analysis — "The Score Is a Mirror" Deep Dive

Date: 2026-08-10
Level: A (research-only diagnostic)
Layer: Research
Status: applied — no production, promotion, locked-OOS, shadow, broker or public-surface decision

## Purpose

The two 2026-08-10 batteries produced five findings (R1, Q3, R4, F1, M2) that
together suggested a clean story: **"the score is not a predictor, it is a
mirror of what already happened."** This battery decomposes that claim into a
causal chain and tries to break each link, then attacks the whole thesis with
alternative explanations.

Runner: `research/mirror_analysis_2026_08_10.py`. Tests:
`tests/test_mirror_analysis_2026_08_10.py` — 7/7 pass.
Artifact: `data/backtest_out/mirror_analysis_2026-08-10.json`. 9/9 COMPLETED.

## The honest headline

**The "mirror" thesis is directionally right but mechanistically wrong — and
the correction is more damaging than the original claim.**

The score is not a clean mirror of the past that could simply be inverted or
re-anchored. It is something worse for a selection product: **a near-zero
forward-information signal whose largest single component is extension, but
which is not reducible to extension, not fixable by fading, and not explained
by data artifacts, bad days, horizon, or liquidity.**

## The causal chain, link by link

### L1 — Does the score encode extension? **YES, but only ~half.**
- `dist_52w_high` ρ = **0.667**, `past_5d_pct` ρ = **0.375** — the two biggest
  components are both backward-looking.
- But extension alone explains only **R² = 0.477** of the score's rank. The
  rest is a mix of lottery (-0.25), atr_pct (-0.22), gap (0.20), rvol (0.18).
- **Correction to the thesis:** the score is not *purely* a mirror. It is a
  backward-looking-*tilted* composite with no dominant forward component.

### L2 — Does extension reverse? **NO clean gradient at 5d.**
- `dist_52w_high` quintiles vs forward 5d: near-high q1 median **-0.59%**,
  but q2–q5 are all positive and non-monotone; overall Spearman **+0.024**.
- `past_5d` quintiles: the "ripped" q5 median is **0.00%** (weakest), but the
  gradient is weak and non-monotone.
- **Correction to the thesis:** the simple "extension → reversal" mechanism
  (which M2's gap-up finding hinted at) does **not** generalize across the
  extension measures. The mirror does not cleanly fade.

### L3 — Does the score add anything beyond extension? **Ambiguous, and that is the point.**
- Raw Spearman(score, fwd 5d) = **0.013**.
- Partial Spearman(score, fwd | dist_52w_high, past_5d) = **0.025**.
- Controlling for the mirror does not reveal hidden forward information; the
  residual is still ~zero. The score is not "extension + signal"; it is
  "extension + noise."

### L4 — Is it the score or the selection layer? **The score band drives it; eligibility adds nothing.**
- Within the **top score quintile**: eligible median **-0.20%** vs
  not-eligible median **+1.08%**. The selection layer does not rescue the
  score; if anything it picks the worse members of the best band.
- Across the grid, eligible cells are tiny (n=0–118) and consistently worse
  than their not-eligible counterparts at the same score level.
- **This is the most damaging single result for the selection product:** the
  problem is not "good score, bad selection." The score band itself carries
  the (non-)information, and `entry_ok` selects adversely *within* it.

## Alternative explanations — all rejected

| Alternative | Test | Result | Verdict |
|---|---|---|---|
| A1: data artifacts drive it | clean vs flagged symbols | flagged set empty in this export; clean symbols show past 0.376 / fwd 0.013 | **Rejected** — not an artifact |
| A2: a few bad days | per-day score→fwd Spearman | 24 days, median +0.018, 54% positive, tightly clustered near zero | **Rejected** — it is near-zero on *most* days, not negative on a few |
| A4: horizon-specific | 1/2/3/5/10d | score→fwd ρ = 0.013–0.038 at *every* horizon | **Rejected** — no horizon rescues it |
| A5: liquidity/size proxy | control for rvol + atr_pct | partial ρ = **0.003** | **Rejected** — vol/liquidity does not explain the non-information |

## The synthesis test — the thesis's own prediction fails

If the score were a true mirror, **fading it should beat following it.**
- Spearman(follow score) = **+0.013**
- Spearman(fade extension) = **-0.008**
- Top-decile follow: median **+0.77%**; top-decile fade: median **-0.89%**.

**Following the score beats fading it.** The mirror thesis, taken literally,
makes a prediction that the data rejects. The score is not a mirror you can
invert — it is closer to **noise with a backward-looking tilt**.

## What this actually means (the corrected picture)

1. **The score is not a predictor.** Forward information is ~0 at every
   horizon, on most days, on clean data, controlling for extension and
   liquidity. (R1, A1, A2, A4, A5)
2. **It is not a clean mirror either.** It is not reducible to extension
   (L1 R²=0.48), extension does not cleanly reverse (L2), and fading it loses
   (SYNTH). So "just invert it" is not a strategy.
3. **The selection layer is adversely selective within score bands** (L4).
   `entry_ok` picks the worse members of the best band. This is a separate,
   additional defect on top of the score's emptiness.
4. **The composite is mostly backward-looking + noise.** The most honest
   one-line description: *"a slow-moving measure of recent extension, plus
   several weak factors, with no net forward information."*

## Why this is worse than "mirror"

A mirror would be useful — you could invert it, or use it as a contrarian
signal, or at least as a stable descriptive anchor. The data rejects all
three. A near-zero-information composite that *looks* like a signal (because
it co-moves with recent winners) is the most dangerous kind: it invites
confidence it cannot repay, and it cannot be cheaply fixed by inversion,
re-weighting, or selection tweaks.

## Consequences

- **Score parameter tuning is now triply indefensible** (no forward info, not
  invertible, selection adversely selective within bands). Frozen until a
  forward-looking target exists.
- **The "selector" product identity is contradicted at the band level** (L4),
  not just the portfolio level (battery-1 P1). This is a Level B product-rule
  question, not made here.
- **The only measurable structure remains in the path** (battery-1 X1/X3) and
  in construction (battery-2 P2 ATR-parity). Both are gated behind the
  data-integrity work (E2/V0), which this battery's A1 result makes *more*
  urgent, not less — because it rules out "the artifacts did it" as an excuse.

## Governance boundary

No scanner, score, entry/exit, risk, portfolio, publication, OOS, shadow,
broker, paper/live or public behavior was changed. All code is new and
isolated under `research/` + `tests/`; artifacts under `data/backtest_out/`.
Any rule change derived from these findings requires Level B/C approval.
