# Strategic Thinking Lab — Experiment Battery Results

Date: 2026-08-10
Level: A (research-only diagnostic)
Layer: Research
Status: applied — no production, promotion, locked-OOS, shadow, broker or public-surface decision

## Scope and rules

This battery executes the **feasible subset** of the 2026-08-10 Strategic
Thinking Lab experiment list against the canonical export
(`data/backtest_out/full_universe_enriched.csv`, 53,859 raw rows → 27,386
deduplicated symbol-days, 2025-09-11..2026-07-13) and the daily price cache.

Rules enforced by construction (`research/strategic_lab_2026_08_10.py`):

- no new parameter search; frozen fields + deterministic forward-path metrics;
- robust statistics (median, 1%/99% winsorized mean, positive rate);
- date-block bootstrap CIs (1,000 draws, seed 20260810) because rows within a
  scan date are cross-sectionally correlated;
- nothing here is a strategy claim; every result is a diagnostic.

Focused synthetic tests: `tests/test_strategic_lab_2026_08_10.py` — 8/8 pass.
Artifact: `data/backtest_out/strategic_lab_2026-08-10.json`.

## Headline findings

| # | Finding | Evidence |
|---|---------|----------|
| 1 | **The score is backward-looking.** Spearman(finpilot_score, past 5d return) = **0.376**; Spearman(score, forward 5d return) = **0.013** (n=16,693, flagged symbols excluded). The score mostly measures what already happened. | R1 |
| 2 | **Selection does not beat chance.** Per-date, the eligible portfolio underperforms random same-date rejected portfolios: median difference **-2.01pp**, positive on only **31%** of 35 dates (net of 0.55% cost). | P1 |
| 3 | **Reverse-ranking direction replicates, but is not statistically decisive.** Eligible median -0.386% (block CI [-1.69, +1.46]) vs rejected +0.427% (CI [-0.00, +0.99]). CIs overlap; direction matches the 2026-08-07 decision-quality finding. | R2 |
| 4 | **Score deciles are not monotone** in forward return (decile-vs-median Spearman 0.33). | R3 |
| 5 | **Ranks are sticky**: day-over-day rank Spearman = **0.742** (14,993 pairs) — the score largely repeats yesterday, consistent with a slow-moving backward-looking measure. | R4 |
| 6 | **Neither absolute score nor within-day percentile carries forward information** (0.013 vs -0.040). | R10 |
| 7 | **Entry timing is not the problem at daily scale**: next-open vs signal-close median cost = **-0.12pp** on eligible. | E1 |
| 8 | **Price-data integrity matters more than signal**: restricting eligible to |drift| ≤ 1% (68% kept) moves the median from -0.39% to **+0.52%**. | E2 |
| 9 | **A real opportunity window exists but is not captured.** Eligible 5d MFE median **+4.26%**, MAE median **-4.36%**; median time-to-MFE = 3 days. Holding to horizon captures only **~14%** of the typical favorable excursion (X3). | X1/X3 |
| 10 | **A naive invalidation exit does not fix it**: -1 ATR daily-close stop proxy worsens the median (-0.63% vs -0.39%) and stops 90% of candidates. | X6 (PARTIAL, daily-bar proxy) |
| 11 | **Losses cluster in time**: 35% of eligible dates have majority losses; lag-1 autocorrelation of daily mean = 0.23. | P7 |
| 12 | **Same-day candidates are not highly correlated** (median pairwise 20d return correlation 0.19) — redundancy is not the main portfolio problem; selection is. | P2 |
| 13 | **Effective sample size is ~44x smaller than row count for the full universe** (27,361 rows → ~620 effective) and ~4.8x smaller for eligible (799 → ~168). Naive CIs understate uncertainty accordingly. | S1 |
| 14 | **Label semantics are unverified**: resolved_pct_t5 vs cache close-to-close 5d return correlate at only 0.86 (median abs diff 3.6pp). All resolved_*-based results carry this caveat. | V0 |
| 15 | **Regime effects exist but are inconsistent**: mid-volatility regime cells show positive medians (+0.97% to +1.38%) while high-vol mid-tercile is negative; eligible regime cells are too small (n=13/40) for conclusions. | G2/G4 |

## Interpretation (diagnostic, not promotion)

The battery converges on the Strategic Thinking Lab's central suspicion:

1. **The ranking layer measures the past, not the future** (R1, R4, R10, R3).
   Optimizing entry/exit/TP/SL on top of a backward-looking score cannot
   produce forward edge; the War Room question "what does the score actually
   measure?" now has an empirical answer: mostly prior 5-day movement.
2. **The selection layer currently subtracts value** relative to same-date
   random rejection (P1), consistent with the earlier 41.8% false-rejection
   finding. This is a product-identity-level fact: the "selector" claim is
   not supported.
3. **The tradeable phenomenon may be in the path, not the endpoint** (X1/X3):
   eligible candidates show a +4.3% median favorable excursion within 5 days
   that a hold-to-horizon rule captures only ~14% of. This motivates
   path-aware targets (time-to-event, MFE-capture, adverse-excursion
   avoidance) rather than better endpoint prediction — but only after the
   data-integrity gate (E2, V0) is closed, because drift and label
   verification move results as much as any signal.
4. **All uncertainty statements must use block-resampled or effective-sample
   sizes** (S1); row-count-based significance is illusory in this dataset.

## Experiment register

| Experiment | Status | Key result |
|---|---|---|
| V0 label validation | COMPLETED | corr 0.86 — semantics unverified |
| R1 backward vs forward | COMPLETED | past 0.376 / fwd 0.013 |
| R2 reverse ranking | COMPLETED | direction replicates, CIs overlap |
| R3 decile monotonicity | COMPLETED | not monotone (0.33) |
| R4 rank stability | COMPLETED | 0.742 sticky |
| R5 signal decay | COMPLETED | no clean horizon pattern; eligible medians ≈ 0 at all horizons |
| R10 cross-sectional vs absolute | COMPLETED | neither informative |
| E1 entry delay | COMPLETED | delay cost small (-0.12pp median) |
| E2 drift budget | COMPLETED | ≤1% drift subset median +0.52% |
| X1 MAE/MFE layer | COMPLETED | MFE +4.26% / MAE -4.36% median (5d) |
| X3 MFE capture | COMPLETED | ~14% captured |
| X6 invalidation exit | PARTIAL | daily-bar proxy; worsens median |
| G2 regime calibration | COMPLETED | inconsistent across regimes |
| G4 regime-stratified eligible | COMPLETED | insufficient cell sizes |
| P1 counterfactual portfolio | COMPLETED | selection < random (31% positive dates) |
| P2 candidate correlation | COMPLETED | median 0.19 — low redundancy |
| P7 loss clustering | COMPLETED | clustering present (0.23) |
| S1 effective sample size | COMPLETED | n_eff ≈ 620 (universe) / 168 (eligible) |

## Blocked experiments (not runnable in this battery)

**Blocked — data does not exist:**
- Intraday entry/exit variants (E3–E7, E9, E10), signal half-life at
  minute/hour scale, auction features: require intraday OHLCV.
- Spread/impact/ADV-based capacity and executable-universe layers: observed
  spread rate is 0% in current data.
- Gap/event taxonomy (M3): requires earnings/news event labels.
- G1 vol_regime backfill: requires production export change (Level B).

**Blocked — requires users (product/behavioral track):**
- PR1–PR7 (interviews, positioning A/B, concierge MVP, pricing, churn,
  AI-substitution test) and B1–B7 (Grade vs evidence-card, counter-thesis,
  outcome-blind review, pre-commitment, no-signal day, calibration score,
  friction). These are the highest-information experiments in the lab and
  cannot be executed by an agent; they need 10–15 real users.

**Blocked — requires LLM evaluation harness:**
- Grounded-rationale audit, adversarial research agent, AI-free baseline.

## Consequences for the BIG BETs

- **Bet #1 (Truth Layer)** is strengthened: E2 and V0 show data integrity and
  label verification move results more than any signal parameter.
- **Bet #4 (Counterfactual Selection Audit)** is now answered at diagnostic
  level: selection currently does not add value (P1, R2). The "selector"
  product identity is unsupported by evidence.
- **New research direction with the best evidence support**: path-aware
  targets (MFE capture, time-to-event, adverse-excursion avoidance) — but
  gated behind data-integrity repair, not parallel to it.
- **Ranking-layer parameter work should stay frozen** until a forward-looking
  target exists; R1/R4/R10 show the current score cannot support it.

## Governance boundary

No scanner, score, entry/exit, risk, portfolio, publication, OOS, shadow,
broker, paper/live or public behavior was changed. All code is new and
isolated under `research/` + `tests/`; artifacts live under
`data/backtest_out/`. Any rule change derived from these findings requires
the applicable Level B/C approval.
