# RESEARCH-X/H2 — Score-Direction Test Result

**Tarih:** 2026-09-21
**Status:** historical split-sample; true future-OOS değil
**Pre-registration:** `reports/research_x_h2_score_direction_preregistration_2026-09-21.md`
**Runner:** `research/research_x_h2_score_direction_2026_09_21.py`

**Overall H2a verdict:** `NOT_SUPPORTED`

Bu rapor yalnızca preregistered `composite_score` quantile/outcome ölçümünü verir. `ranking_score` eşdeğerliği, reverse score veya production kuralı sonucu çıkarılmaz.

## Fold sonuçları

### F1 — `OK`

Train: `['2026-05-01', '2026-05-31']` · Test: `['2026-06-01', '2026-06-30']` · n=10077

| Quantile | n | Median c2c_5d | Mean | P(<0) | P(<=-10) | P(>=+10) |
|---|---:|---:|---:|---:|---:|---:|
| Q1 | 3086 | 1.412031 | 11.859098 | 0.41348 | 0.085872 | 0.152301 |
| Q2 | 1542 | 1.054485 | 12.217913 | 0.411803 | 0.098573 | 0.132296 |
| Q3 | 2144 | 0.503526 | 1.373953 | 0.454757 | 0.119869 | 0.127332 |
| Q4 | 1922 | 0.582065 | -0.044292 | 0.454735 | 0.112903 | 0.098335 |
| Q5 | 1383 | 0.870356 | 1.320867 | 0.433116 | 0.100506 | 0.101952 |

Q1−Q5 median: `0.541675` · adjacent inverse pairs: `2/4` · Spearman: `-0.6`

Secondary Q1−Q5 contrasts: big-winner `0.050349` · big-loser `-0.014634` · negative-rate `-0.019636`

Train unique scores: `55` · cutpoints: `[13.0, 26.0, 42.0, 53.0]` · test bin counts: `[3086, 1542, 2144, 1922, 1383]` · boundary shares: `{'q20': 0.020542, 'q40': 0.012305, 'q60': 0.017862, 'q80': 0.014091}`

**Date-block bootstrap (B=2,000) Q1−Q5 CI:**
median `[-0.603244, 1.509694]` · mean `[2.3116, 18.7717]` · P(<0) `[-0.087645, 0.050008]` · P(<=-10) `[-0.045359, 0.009228]` · P(>=+10) `[-0.011282, 0.091039]`

**Matched-date randomized ordering (R=1,000):** primary median raw one-sided p=`0.092907` · big-winner raw one-sided p=`0.000999` · null median CI=`[-0.256095, 0.713854]` · big-winner CI=`[-0.015867, 0.02692]` · big-loser CI=`[-0.014913, 0.022662]` · negative-rate CI=`[-0.043703, 0.015173]`

### F2 — `OK`

Train: `['2026-05-01', '2026-06-30']` · Test: `['2026-07-01', '2026-07-31']` · n=16555

| Quantile | n | Median c2c_5d | Mean | P(<0) | P(<=-10) | P(>=+10) |
|---|---:|---:|---:|---:|---:|---:|
| Q1 | 4800 | -0.995583 | 13.855419 | 0.567292 | 0.1275 | 0.062292 |
| Q2 | 3678 | -0.529336 | 3.032065 | 0.540783 | 0.112833 | 0.05764 |
| Q3 | 4756 | -0.816716 | -1.096653 | 0.567704 | 0.116064 | 0.041211 |
| Q4 | 2131 | -0.701548 | -1.797815 | 0.564524 | 0.098545 | 0.033318 |
| Q5 | 1190 | -0.587709 | -1.289172 | 0.556303 | 0.079832 | 0.032773 |

Q1−Q5 median: `-0.407874` · adjacent inverse pairs: `1/4` · Spearman: `0.4`

Secondary Q1−Q5 contrasts: big-winner `0.029519` · big-loser `0.047668` · negative-rate `0.010989`

Train unique scores: `90` · cutpoints: `[9.0, 24.0, 40.0, 51.0]` · test bin counts: `[4800, 3678, 4756, 2131, 1190]` · boundary shares: `{'q20': 0.018907, 'q40': 0.01492, 'q60': 0.012987, 'q80': 0.011114}`

**Date-block bootstrap (B=2,000) Q1−Q5 CI:**
median `[-1.304951, 0.519909]` · mean `[8.584575, 22.68026]` · P(<0) `[-0.083986, 0.092699]` · P(<=-10) `[0.01249, 0.075496]` · P(>=+10) `[0.005063, 0.047814]`

**Matched-date randomized ordering (R=1,000):** primary median raw one-sided p=`0.984016` · big-winner raw one-sided p=`0.000999` · null median CI=`[-0.367597, 0.540659]` · big-winner CI=`[-0.036479, -0.007319]` · big-loser CI=`[-0.021535, 0.017298]` · negative-rate CI=`[-0.036165, 0.025687]`

## Pooled diagnostic

Fold-specific train cutpoints remain primary. This pooled table is a predeclared diagnostic for whether the inverse pattern is driven by one endpoint bin.

| Quantile | n | Median c2c_5d | Mean | P(<0) | P(<=-10) | P(>=+10) |
|---|---:|---:|---:|---:|---:|---:|
| Q1 | 7886 | -0.162156 | 13.074206 | 0.507101 | 0.11121 | 0.097515 |
| Q2 | 5220 | -0.07246 | 5.745586 | 0.502682 | 0.108621 | 0.079693 |
| Q3 | 6900 | -0.392636 | -0.328975 | 0.532609 | 0.117246 | 0.067971 |
| Q4 | 4053 | -0.149081 | -0.966265 | 0.51246 | 0.105354 | 0.06415 |
| Q5 | 2573 | 0.06832 | 0.113736 | 0.490089 | 0.090944 | 0.069957 |

Pooled Q1−Q5 median: `-0.230476` · adjacent inverse pairs: `1/4` · Spearman: `0.5`

## Guardrails

- Score field: `composite_score`; no score refit, inversion, flag change or production change.
- Fold design is chronological but historical; it is not true future-OOS.
- Empty bins or insufficient dates remain explicit blockers; no post-hoc quantile/threshold repair was applied.
- H2d remains deferred until H2a-c, tie-resolution and `ranking_score` mapping are separately resolved.

## Governance

Read-only research artifact. Negative, mixed or insufficient results are valid outcomes; no production promotion follows from this report.
