# Outlier Dependence Audit v1: Baseline (Investor Question 5)

- Date: 2026-10-14
- Status: read-only audit. No production code, strategy parameter, database row, sealed dataset, existing result or publication was changed or executed.
- Layer: research evidence (Layer 5). Risk & Compliance unchanged.
- Level: A (read-only analysis and reports).

## 1. Trade unit and return field

| Item | Definition used | Evidence |
|---|---|---|
| Unit of analysis | Decided archived signal: `signals_archive` rows with `resolved_status_barrier` in {`resolved_win`, `resolved_loss`} and non-null `resolved_pct_barrier` | 5,206 rows |
| Return field | `resolved_pct_barrier` (gross, per signal, stored value) | Stored value equals take-profit/entry - 1 (wins) or stop-loss/entry - 1 (losses) for all 5,206 rows (tolerance 0.05 pp) |
| Executed trades | None. These are simulated barrier outcomes, not realized P&L | `alpaca_orders`: 11 rows, 0 fills; `trades`, `positions`, `execution_events` empty |
| Costs | None in the stored return | Q3 audit |
| Position sizing | None. Each signal has equal weight and no notional | Q3 audit |
| Excluded | 10 expired and 532 unresolved rows (not in the denominator) | archive status counts |
| Overlap | Multiple signals per symbol and day are retained. Overlap was not recounted for the decided-only subset | Q3 audit reports 5,748 rows on 4,318 symbol-days for the full archive |

## 2. Baseline results (n = 5,206)

| Metric | Value |
|---|---|
| Mean gross return per signal | +0.3984 % |
| Median gross return | -0.6431 % |
| Sum of returns | +2,074.2 pp |
| Hit rate (`resolved_win`) | 30.06 % (1,565 wins) |
| Losses | 3,641 |
| Average win | +4.2825 % |
| Average loss | -1.2711 % |
| Profit factor (sum of positive / absolute sum of negative) | 1.448 |
| Win/loss asymmetry | 3.369 (matches the Q3 audit) |
| 95 % bootstrap CI of mean, clustered by signal date (37 dates, B = 2,000, seed 20261014) | [+0.064 %, +0.565 %] |

The mean is positive while the median is negative. The positive mean depends on the right tail of the distribution (see the sensitivity report).

## 3. Time concentration

- Decided rows by month: 2025-09: 1,579; 2025-10: 474; 2025-11: 6; 2025-12: 6; 2026-03: 2,495; 2026-04: 177; 2026-05: 469. No decided rows appear in 2026-01, 2026-02 or from 2026-06 onward in this table.
- Weekday of the signal date: Sunday 2,102 (40.4 %), Saturday 197, Monday 813, Tuesday 885, Wednesday 589, Thursday 251, Friday 369.
- Rows with a signal date on a non-trading day (Saturday or Sunday): 2,299 (44.2 %). These rows have no same-day price bar in `data/price_cache`.
- Signal dates 2026-03-01 (Sunday) and 2026-03-03 (Tuesday) together contain 2,421 rows (46.5 %). Their mean is +0.707 %, median -1.029 %, hit rate 33.25 %.
- Excluding those two dates leaves 2,785 rows with mean +0.130 %, median -0.537 %, hit rate 27.29 %.
- Not verified: whether the 2026-03 records were written at signal time or back-filled. The table holds no creation timestamp. Status: UNVERIFIED.

## 4. Symbol concentration

- Distinct symbols: 1,017.
- Top 10 symbols by net return sum: 32.23 % of the net sum.
- Top 10 symbols by row count: 7.55 % of rows.

## 5. Reproduction against cached daily bars

- Every archived symbol has a file in `data/price_cache`. 529 bar rows were skipped because they lacked a date, open, high, low, close or volume value.
- Replay rule tested: first bar after the signal date, up to 30 trading bars, take-profit checked before stop-loss on the same bar, exit at the barrier.
- Result: 4,631 of 5,206 rows (88.9 %) match the stored status. 575 rows (11.0 %) do not match: 546 replay as win while stored as loss, 27 replay as loss while stored as win, and 3 have no hit within the window.
- Alternative conventions tested (matches out of 5,206): 21 bars 4,630; include signal-day bar 4,204; stop-first 4,611; 30 bars stop-first 4,612; include signal-day bar with stop-first 4,220. No convention reproduces all rows.
- Hypotheses, not verified: (a) price vintage or dividend/split adjustment (the cache holds 195 files with `adjusted_close`, and the cache file was written 2026-07-30, after the archive resolution); (b) equality at the barrier. The UNP example (2026-03-01 signal, replay high 268.14 on 2026-03-02 versus take-profit 268.03, stored as loss) is not explained by equality.
- Consequence: the stored `resolved_pct_barrier` is used as the primary return field, consistent with the Q3 audit. Replay is used only for execution sensitivities, on the 4,631 matched rows. The 11 % reproduction gap is a stated limitation.

## 6. Method definitions

- Top 1 %: the first floor(0.01 x 5,206) = 52 rows when ranked descending by `resolved_pct_barrier`. The cut value is +13.2075 %, with one row at that value.
- Top 5 %: the first floor(0.05 x 5,206) = 260 rows. The cut value is +6.3477 %, with one row at that value.
- Only these two cut-offs were computed. No other cut-off was tested.
- The replay convention (30 bars, take-profit first) was selected as the best of six tested conventions. It is therefore post-hoc and is used only for the execution sensitivities, not for the baseline return.

## 7. Limitations

- Gross barrier labels, ideal fills, no costs, no sizing, overlapping signals.
- Returns are simulated barrier outcomes. They are not realized P&L.
- Survivorship and point-in-time membership of the universe: not verified.
- Price data source and adjustment policy: not verified against the resolver at resolution time.
