# Ten-Perspectives Lab — Experiment Battery Results

Date: 2026-08-10
Level: A (research-only diagnostic)
Layer: Research
Status: applied — no production, promotion, locked-OOS, shadow, broker or public-surface decision

## Scope

Second battery covering the **feasible, not-yet-run** experiments from the
2026-08-10 "10-Perspective Independent Brainstorming & Red-Team" report.
Experiments already executed in `reports/strategic_lab_experiments_2026-08-10.md`
(R1–R5, E1/E2, X1/X3/X6, G2/G4, P1/P2/P7, S1) are not duplicated. User-facing
(PR/B series), LLM-facing (grounding/adversarial) and intraday/spread/event
experiments remain **BLOCKED** for the reasons recorded in the first report.

Runner: `research/ten_perspectives_lab_2026_08_10.py` (reuses the strategic
lab's loaders, path-metric enrichment and block-bootstrap statistics; frozen
fields only, no parameter search). Tests:
`tests/test_ten_perspectives_lab_2026_08_10.py` — 10/10 pass.
Artifact: `data/backtest_out/ten_perspectives_lab_2026-08-10.json`.
All 13 experiments COMPLETED.

## Headline findings

| # | Finding | Exp |
|---|---------|-----|
| 1 | **The score's probability mapping is worse than the base rate.** Out-of-sample Brier skill vs a constant base-rate predictor: **-0.019** (P(positive)) and **-0.030** (P(beats cost)). The score does not just fail to calibrate — it subtracts predictive value relative to doing nothing. | F1 |
| 2 | **Eligible candidates do not beat SPY over the same window**: median relative return **-1.22pp**, block-bootstrap CI [-2.11, -0.23] — statistically below zero. vs IWM: -0.86pp, CI [-1.67, +0.07]. (Simple subtraction, not beta-neutral.) | Q5 |
| 3 | **The score encodes extension, not opportunity**: strongest encoded features are `dist_52w_high` (ρ=0.667) and `past_5d_pct` (ρ=0.376). The features with the most *forward* information are `lottery_factor` (ρ=**-0.110**) and `overnight_gap_factor` (ρ=**-0.095**) — both negative. | Q3 |
| 4 | **The best failure predictor is `lottery_factor`** (ρ=0.184 with failure), then `overnight_gap_factor` (0.126) and `atr_pct_real` (0.109). `finpilot_score` itself: -0.030 — noise. | Q2 |
| 5 | **The score carries no adverse-movement information** (ρ=0.006). Adverse excursion ≤ -1 ATR within 5 days is nearly universal (base rate 86.5%; eligible 91.2%) — the 1-ATR stop class is structurally fragile at this horizon. | Q1 |
| 6 | **High-rvol eligible candidates are the worst cohort**: high-rvol tercile median **-1.77%** (38.7% positive) vs low-rvol **+0.68%** (54.3%). Relative volume conditions outcomes *negatively* in the selected cohort. | M1 |
| 7 | **Big gap-ups fail, big gap-downs bounce** (eligible): gap_up ≥3% → median **-3.04%**, 29.4% positive (n=85); gap_down ≥3% → median **+3.05%**, 66.7% positive (n=51). An extension/reversal pattern the current score rewards in the wrong direction. | M2 |
| 8 | **First-passage is a coin flip for eligible** (P(MFE before MAE) = 0.494; rejected 0.439). Daily bars cannot resolve intraday ordering; the small gap is consistent with the weak MFE-capture story from X1/X3. | Q6 |
| 9 | **Correlation-cluster selection does not rescue the portfolio** (cluster-minus-all median 0.0, positive on 38.7% of dates) — redundancy was never the binding constraint (P2 in battery 1). | P1 |
| 10 | **ATR-parity sizing dominates on risk**: max drawdown **-15.9%** vs -24.3% equal-weight, with the best daily Sharpe (0.267). Score-weighted sizing has the best median day (+0.87%) but worse drawdown (-20.2%). All schemes' means are outlier-driven (mean ≈ 4% vs median ≈ 0.1–0.9%). | P2 |
| 11 | **Tails are fat on both sides of the selection boundary**: eligible CVaR5 **-21.3%** vs rejected -22.9% — selection improves the 5% tail by only ~1.6pp. | P3 |
| 12 | **Unsupervised regimes mostly isolate data artifacts**: k-means on (atr_pct, rvol, gap, past_5d) produced clusters of n=18, n=1, n=1 with extreme means — the dominant "regimes" in this dataset are price-data anomalies, echoing the F9 integrity gate. | A1 |
| 13 | **Null-feature injection calibrates the noise floor**: at n=27,361 the spurious-correlation p95 is |ρ|=0.011. Most features exceed it, but the strongest real forward correlation (0.110) is still small in absolute terms — detectable ≠ useful. | Q4 |
| 14 | **`catalyst_factor` is a dead feature** (constant 0.0 across the export) — it occupies score weight while carrying zero information. | Q3 |

## Cross-battery synthesis (with strategic_lab_2026-08-10)

The two batteries now triangulate the same conclusion from independent angles:

1. **Backward-looking score** (R1: past ρ=0.376 vs fwd ρ=0.013) is now
   *explained* (Q3): the score encodes 52-week-high distance and recent 5-day
   movement — i.e., extension. Its most forward-informative components point
   *downward* (lottery/overnight-gap negative). M2 shows the behavioral
   consequence: the score rewards big gap-ups that systematically mean-revert.
2. **Selection subtracts value** (battery-1 P1: -2.01pp vs random; R2
   direction) and now also **underperforms the benchmark** (Q5: -1.22pp vs
   SPY, CI below zero) and **fails calibration against the base rate** (F1).
   Three independent failure modes of the same layer.
3. **The path, not the endpoint, remains the only place with measurable
   structure** (X1/X3: +4.26% median MFE, ~14% captured; Q6: first-passage
   ≈ coin flip; Q1: adverse excursions near-universal). Any future edge
   claim must be path-aware and must survive the data-integrity gate (E2/V0).
4. **Sizing and risk mechanics (P2: ATR-parity drawdown -15.9% vs -24.3%)
   dominate selection as a lever** — consistent with the portfolio-manager
   persona's hypothesis that construction > selection.
5. **Effective sample sizes (S1: ~620 universe / ~168 eligible) apply to all
   of the above**; every CI in this battery is block-bootstrapped.

## Experiment register

| Experiment | Status | Key result |
|---|---|---|
| Q1 adverse-movement target | COMPLETED | score ρ=0.006; base adverse rate 86.5% |
| Q2 failure prediction | COMPLETED | lottery_factor ρ=0.184 strongest; score noise |
| Q3 score semantics | COMPLETED | encodes extension (52w-high 0.667); forward info negative |
| Q4 null-feature injection | COMPLETED | null p95 |ρ|=0.011; strongest real 0.110 |
| Q5 benchmark-relative | COMPLETED | vs SPY -1.22pp median, CI below zero |
| Q6 first-passage survival | COMPLETED | P(MFE first)=0.494 eligible |
| F1 calibration/reliability | COMPLETED | Brier skill vs base rate negative |
| P1 correlation-cluster selection | COMPLETED | no improvement (38.7% positive dates) |
| P2 sizing comparison | COMPLETED | ATR-parity best drawdown (-15.9%) |
| P3 tail metrics | COMPLETED | eligible CVaR5 -21.3% |
| M1 rvol conditioning | COMPLETED | high-rvol eligible worst (-1.77% median) |
| M2 gap conditioning | COMPLETED | gap-up≥3% fails (-3.04%); gap-down≥3% bounces (+3.05%) |
| A1 unsupervised regimes | COMPLETED | clusters isolate data artifacts |

## Still blocked (unchanged from battery 1)

- **User track (PR1–PR7, B1–B7)** — requires 10–15 real users; highest
  information gain per unit cost in the entire lab.
- **Intraday/microstructure track** — requires intraday OHLCV, spread/impact,
  event labels.
- **LLM track** — grounded-rationale audit, adversarial agent, AI-free
  baseline; requires an evaluation harness decision.

## Consequences

- The ranking/selection layer now has **five independent counter-evidence
  lines** (R1, R2/P1-battery-1, Q3, Q5, F1). Continuing to tune its
  parameters is not defensible; the layer needs either a forward-looking
  target rebuild or an explicit "descriptive, not predictive" product
  framing. That is a Level B product-rule decision, not made here.
- `catalyst_factor` being constant-zero is a concrete, cheap audit follow-up
  in the score contract (Level B if the contract changes).
- M2's gap-reversal pattern and M1's rvol-inversion are the only
  forward-looking structures detected; both are small, both need the
  data-integrity gate (E2/V0) closed before any confirmatory run, and both
  would be *new hypotheses* requiring pre-registration, not findings.
- ATR-parity sizing (P2) is a portfolio-construction result, not a trading
  rule; any use requires the standard gate chain.

## Governance boundary

No scanner, score, entry/exit, risk, portfolio, publication, OOS, shadow,
broker, paper/live or public behavior was changed. All code is new and
isolated under `research/` + `tests/`; artifacts live under
`data/backtest_out/`. Any rule change derived from these findings requires
the applicable Level B/C approval.
