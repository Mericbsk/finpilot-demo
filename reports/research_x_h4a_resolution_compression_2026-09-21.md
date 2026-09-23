# RESEARCH-X/H4A - Score Resolution and Compression Audit

**Date:** 2026-09-21
**Level:** A - read-only descriptive research
**Runner:** `research/research_x_h4a_resolution_compression_2026_09_21.py`
**Artifact:** `data/backtest_out/research_x_h4a_resolution_compression_2026-09-21.json`

## Executive Result

H4A VERDICT: `COMPRESSION_SUPPORTED`

Score resolution: N_total = `40014`; N_unique_scores = `90`; raw resolution = `0.002249`.
Tie concentration: tie observation rate = `0.999975`; largest tie = `3244.0`.
Score precision: integer-valued fraction = `1.0`; production final operation = `int(round(strength))`.
Production impact: `UNCHANGED`.

## Research Question

Can the existing production `composite_score` distinguish observations, or are score-level ties and daily compression structurally concentrated? This is a descriptive forensic diagnostic; it does not test a new score.

## Governance

Research / Level A / READ_ONLY. Production mutation, score mutation, ranking mutation, scanner mutation, threshold optimization, and locked-OOS opening are forbidden.

## Verdict

- H4A structural verdict: `COMPRESSION_SUPPORTED`.
- Verdict basis: Descriptive rule: >=99% of observations are in non-singleton score groups, median daily unique-score resolution is <=10%, and median daily tie share is >=90%.
- Global integer scale capacity: `NOT_PROVEN_COMPRESSED`.
- Global row-level tie concentration: `OBSERVED`.
- Daily cross-sectional resolution: `DESCRIPTIVE_CONCENTRATED_TIES`.
- Historical raw-score information loss: `UNVALIDATED`.
- Official production ranking resolution: `DEFINITION_REQUIRED`.

The audit does not reverse, refit, optimize, or promote any score. H2 remains `CLOSED -> NOT_SUPPORTED`; H4A is a structural audit only.

## Dataset

Input: `data/backtest_out/full_universe_enriched_eod_only.csv`
SHA-256: `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`
Raw rows: `79935`
Deduplicated rows: `43551`
Composite non-null rows: `40014`
Composite date range: `['2026-05-06', '2026-08-05']`; dates: `57`
Label basis: `eod_close`
Deduplication: `one row per symbol/scan_date, retaining earliest lexical scan_ts; stable first row on exact ties`

## Score Definition / Provenance

Primary field: `composite_score`. The export stores integer-valued scores, while the raw recommendation score and component breakdown are not persisted. The documented production path is reported as provenance only; it is not modified or refit here.

## Global Resolution

| Metric | Value |
|---|---:|
| Observations | 40014 |
| Unique composite values | 90 / 101 nominal integer values |
| Observed nominal scale coverage | 0.8911 |
| Observed score range | 0.0 to 93.0 |
| Unique-value deficit rate (`1 - unique/N`) | 0.997751 |
| Tie-group observation share | 0.999975 |
| Singleton observation share | 0.000025 |
| Tie groups | 89 |
| Score-frequency HHI | 0.020889 |
| Effective score count (`1/HHI`) | 47.871 |

The `1 - unique/N` value is a unique-value deficit, not the share of rows in non-singleton groups. Both are reported to avoid conflating scale capacity with tie concentration.

### Most Frequent Score Groups

| Score | Observations | Share |
|---:|---:|---:|
| 0.0 | 3244 | 0.081072 |
| 7.0 | 1092 | 0.027290 |
| 9.0 | 1015 | 0.025366 |
| 11.0 | 905 | 0.022617 |
| 5.0 | 889 | 0.022217 |
| 13.0 | 854 | 0.021343 |
| 47.0 | 828 | 0.020693 |
| 33.0 | 788 | 0.019693 |
| 49.0 | 781 | 0.019518 |
| 51.0 | 767 | 0.019168 |

## Temporal Resolution

All score-available dates are included. The `n >= 5` view is retained only for reconciliation with the earlier compression script; it is not the primary contract.

| Scope | Dates | Median unique/N | Mean unique/N | Min | Max | Median tie share |
|---|---:|---:|---:|---:|---:|---:|
| all_dates | 57 | 0.067171 | 0.285854 | 0.033165 | 1.000000 | 0.993377 |
| dates_n_ge_5 | 53 | 0.059912 | 0.231956 | 0.033165 | 1.000000 | 0.994475 |

## Tie Distribution

| Bucket | Score levels | Observations |
|---|---:|---:|
| 500+ | 40 | 30292 |
| 250-499 | 18 | 7517 |
| 100-249 | 9 | 1552 |
| 50-99 | 6 | 416 |
| 10-24 | 6 | 96 |
| 25-49 | 3 | 108 |
| 5-9 | 4 | 22 |
| 2 | 1 | 2 |
| 3-4 | 2 | 8 |
| singleton | 1 | 1 |

## Score Concentration

Score-frequency HHI: `0.020889`; effective score count: `47.871487`; normalized entropy: `0.913256`.
These are score-frequency concentration diagnostics only, not predictive quality metrics.

## Within-Score Outcome Dispersion

Per-score outcome statistics are descriptive. They do not establish causality, a useful ranking rule, or a production decision threshold.

| Score-group class | Observations | c2c_1d median | c2c_1d IQR | c2c_5d median | c2c_5d IQR |
|---|---:|---:|---:|---:|---:|
| singleton | 1 | -2.545211 | -2.545211 to -2.545211 | 2.143336 | 2.143336 to 2.143336 |
| tie_group | 40013 | -0.1114 | -2.075076 to 1.694915 | -0.156189 | -4.546969 to 3.640257 |

## Tie vs Singleton Diagnostic

The table above separates singleton and non-singleton score groups. This is a resolution diagnostic only; it does not establish that either class has better future outcomes.

## Regime Resolution

**regime**

| Value | n | Unique scores | Resolution | Tie share | Status |
|---|---:|---:|---:|---:|---|
| False | 19377 | 65 | 0.003354 | 0.999845 | OK |
| True | 20637 | 85 | 0.004119 | 0.999903 | OK |

**direction**

| Value | n | Unique scores | Resolution | Tie share | Status |
|---|---:|---:|---:|---:|---|
| False | 19896 | 65 | 0.003267 | 0.99995 | OK |
| True | 20118 | 90 | 0.004474 | 0.99995 | OK |

**vol_regime**

| Value | n | Unique scores | Resolution | Tie share | Status |
|---|---:|---:|---:|---:|---|
| 0.0 | 1070 | 73 | 0.068224 | 0.998131 | OK |
| 1.0 | 6368 | 85 | 0.013348 | 0.999372 | OK |
| 2.0 | 24440 | 89 | 0.003642 | 0.999877 | OK |
| <MISSING> | 8136 | 55 | 0.00676 | 0.999385 | OK |


## Stability and Redundancy

Adjacent same-score transition rate: `0.106662` across `38261` symbol transitions.
Adjacent-date rank-pair count: `46`; median Spearman: `0.817705`.

The JSON artifact contains the full supported field-to-composite correlation table. Those correlations are redundancy diagnostics, not predictive validation.

## Fold Results

## Quantile Boundary Collision

Frozen H2 train-derived cutpoints are reused only to count collisions at their existing boundaries. No cutpoint, band, threshold, or score direction is changed.

H2 boundary artifact status: `AVAILABLE_DIAGNOSTIC_ONLY`.
- `F1` test n `10077`, cutpoints `[13.0, 26.0, 42.0, 53.0]`, tie-preserving bins `[3086, 1542, 2144, 1922, 1383]`.
- `F2` test n `16555`, cutpoints `[9.0, 24.0, 40.0, 51.0]`, tie-preserving bins `[4800, 3678, 4756, 2131, 1190]`.

## Production Mapping Boundary

The historical CSV has no persisted `ranking_score`, `legacy_quality_score`, or `ranking_method`. Current code exposes a ranking field and a publication fallback chain, but the scoped evidence does not define whether official resolution means unique score values, complete sort-key tuples, or final displayed ranks.

**Status:** `DEFINITION_REQUIRED`

Therefore the composite diagnostics in this report must not be presented as official production-ranking resolution. That mapping belongs to the deferred H4B surface.

## Score Precision / Rounding Audit

Observed composite values are integer-valued: `1.0` of finite rows. The code path documents normalization by a fixed 16.5 ceiling, clipping to 0-100, and final integer rounding. The historical raw recommendation score and component breakdown are not persisted, so production information loss from that transformation remains `UNVALIDATED`.

## Evidence vs Interpretation

- **EVIDENCE:** Global score frequency is concentrated in 90 observed integer values across 40,014 score observations.
- **EVIDENCE:** 99.9975% of score observations belong to non-singleton score groups.
- **DESCRIPTIVE:** Median daily unique-score resolution is 0.067171 when all score-available dates are included.
- **NOT_PROVEN:** Compression is the cause of predictive failure; increasing resolution would improve returns.
- **UNKNOWN:** Official production ranking resolution cannot be measured from this export.

## Limitations

- Historical split-sample diagnostic; not future-OOS.
- The export does not persist raw recommendation inputs, ranking_score, legacy_quality_score, or ranking_method.
- Unique-score resolution, tie concentration, and production ranking resolution are distinct concepts.
- Outcome dispersion is descriptive and does not establish causality or a predictive ranking rule.
- Regime cross-tabs use only existing fields and mark groups with n < 5 as INSUFFICIENT_N.

## What This Does NOT Prove

1. The composite score is wrong.
2. Score direction is wrong or a reverse score is correct.
3. The ranking formula or scanner is wrong.
4. Compression causes predictive failure or that higher resolution would improve returns.
5. A feature should be removed, weights should change, or production should change.

## Production Impact

`UNCHANGED`: no score, ranking, scanner, flag, scheduler, publication, database, or user-facing behavior was modified; locked OOS remains unopened.

## Next Research Question

H4B: reconstruct the production ranking mapping and measure information loss only after its official resolution definition is established. H4A does not authorize a score change.

## Guardrails

- No score inversion or score refit was performed.
- No quantile boundary or threshold was tuned.
- No causal or return-improvement claim is made.
- No scanner, ranking, flag, scheduler, publication, or user-facing behavior changed.
- H2 remains `CLOSED / NOT_SUPPORTED`; H2d remains deferred.

## Governance

This is a Level A research-only artifact. The result is descriptive and historical; it does not open locked OOS or authorize a production change.
