# Outlier Dependence Audit v1: Top 1 % and Top 5 % Sensitivity

- Date: 2026-10-14
- Status: read-only audit. Results describe archived simulated barrier outcomes, not realized P&L.
- Baseline and definitions: see [outlier_dependence_baseline.md](outlier_dependence_baseline.md).

## 1. Summary

Removing the top 1 % of signals by gross return lowers the mean by about half. Removing the top 5 % turns the mean negative. The top 5 % contributes more than the entire net sum.

## 2. Sample comparison

| Sample | n | Mean | Median | Sum (pp) | Hit rate | Avg win | Avg loss | Profit factor |
|---|---|---|---|---|---|---|---|---|
| Full (baseline) | 5,206 | +0.3984 % | -0.6431 % | +2,074.2 | 30.06 % | +4.2825 % | -1.2711 % | 1.448 |
| Excluding top 1 % (52) | 5,154 | +0.1896 % | -0.6511 % | +977.4 | 29.36 % | +3.7048 % | -1.2711 % | 1.211 |
| Excluding top 5 % (260) | 4,946 | -0.1615 % | -0.6799 % | -798.7 | 26.38 % | +2.9343 % | -1.2711 % | 0.827 |

Changes in the mean:

- Excluding top 1 %: -0.209 pp (-52 % of the baseline mean).
- Excluding top 5 %: -0.560 pp (the mean changes sign).

## 3. Contribution of the tails

| Tail | Rows | Share of net sum | Share of gross positive sum | Mean of tail rows | Median of tail rows |
|---|---|---|---|---|---|
| Top 1 % | 52 | 52.88 % | 16.36 % | +21.09 % | +16.57 % |
| Top 5 % | 260 | 138.51 % | 42.87 % | +11.05 % | +8.71 % |

- All 52 top-1 % rows and all 260 top-5 % rows are `resolved_win`.
- Removing the top 5 % removes more than the entire net sum of +2,074.2 pp. The remainder is -798.7 pp.

## 4. Bootstrap confidence intervals (95 %, clustered by signal date)

Method: resample signal dates with replacement (B = 2,000, seed 20261014), recompute the mean from the resampled rows.

| Sample | Dates | 95 % CI of mean |
|---|---|---|
| Full | 37 | [+0.064 %, +0.565 %] |
| Excluding top 1 % | 37 | [-0.106 %, +0.367 %] |
| Excluding top 5 % | 37 | [-0.423 %, +0.055 %] |

The number of independent clusters is 37. Intervals are wide and the approximation is weak. They are shown only to indicate direction.

## 5. Flat-cost scenarios

A flat cost in percentage points is deducted from each signal return. The scenario values are not a spread or impact model.

| Flat cost per signal | Full | Excluding top 1 % | Excluding top 5 % |
|---|---|---|---|
| 0.20 pp (`_COST_FLAT_PCT` in `scanner/evaluate.py`) | +0.1984 % | -0.0104 % | -0.3615 % |
| 0.55 pp (research scenario) | -0.1516 % | -0.3604 % | -0.7115 % |
| 1.00 pp (research scenario) | -0.6016 % | -0.8104 % | -1.1615 % |

Cost convention caveat: the Q3 audit found conflicting cost conventions across repositories. The 0.20 pp value is the scanner constant, not a verified round-trip cost.

## 6. Composition of the tails

### 6.1 Date concentration (top 1 %)

- 48 of 52 top-1 % rows fall on two dates: 2026-03-01 (21 rows, Sunday) and 2026-03-03 (27 rows, Tuesday).
- Weekday distribution of top-1 % rows: Tuesday 28, Sunday 21, Monday 2, Friday 1.

### 6.2 Date-excluded sensitivity

Excluding signal dates 2026-03-01 and 2026-03-03 (2,421 rows):

| Sample | n | Mean | Median | Hit rate |
|---|---|---|---|---|
| Two dates only | 2,421 | +0.707 % | -1.029 % | 33.25 % |
| Remainder | 2,785 | +0.130 % | -0.537 % | 27.29 % |
| Remainder excluding top 5 % (membership defined on the full sample) | 2,744 | -0.008 % | -0.543 % | 26.20 % |

The mean of the remainder is close to zero before any outlier removal. After removing the top 5 % of the full sample from the remainder, it is also close to zero.

### 6.3 Symbol and price composition

- Top 1 % symbols with the most rows: AIFU 3, AEHR 3, AUR 3, OCUL 2, ASTS 2, AURA 2, and 4 further symbols with one row each.
- Top 1 % entry price: median 1.78 USD. 17 of 52 rows (32.7 %) have entry below 1 USD, 20 (38.5 %) between 1 and 5 USD, and 15 (28.8 %) at or above 5 USD.
- Full sample: 52 of 5,206 rows (1.0 %) below 1 USD.
- Top 5 %: 31 of 260 rows (11.9 %) below 1 USD.

### 6.4 Time profile (monthly, full versus excluding top 5 %)

| Month | n | Mean (full) | n (excluding top 5 %) | Mean (excluding top 5 %) |
|---|---|---|---|---|
| 2025-09 | 1,579 | +0.042 % | 1,569 | -0.037 % |
| 2025-10 | 474 | +0.119 % | 471 | +0.070 % |
| 2025-11 | 6 | -0.350 % | 6 | -0.350 % |
| 2025-12 | 6 | +0.624 % | 6 | +0.624 % |
| 2026-03 | 2,495 | +0.657 % | 2,275 | -0.377 % |
| 2026-04 | 177 | +0.384 % | 176 | +0.348 % |
| 2026-05 | 469 | +0.518 % | 443 | +0.048 % |

The 2026-03 month carries the positive mean. Excluding its top 5 % turns the month negative. Small monthly samples (6 rows) carry no weight.

## 7. Limits of this sensitivity

- Sensitivity is computed on gross barrier labels with ideal fills.
- The top-tail definition is by stored return. It is not a choice of a different performance measure.
- Tail membership depends on the stored labels, which replay reproduces for 88.9 % of rows (see the baseline report, section 5).
- Only cut-offs of 1 % and 5 % were computed. No further cut-off was tested.

## 8. Conclusion for this report

The sign of the mean depends on the top 5 % of signals. The result is sensitive to outliers and to the date concentration. Execution feasibility of the tail trades is assessed in [execution_feasibility_audit.md](execution_feasibility_audit.md).
