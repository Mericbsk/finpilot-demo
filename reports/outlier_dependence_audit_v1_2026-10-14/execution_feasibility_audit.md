# Outlier Dependence Audit v1: Execution Feasibility

- Date: 2026-10-14
- Status: read-only audit. No order, trade, publication or data change.
- Baseline and definitions: see [outlier_dependence_baseline.md](outlier_dependence_baseline.md). Sensitivities: see [top_1pct_top_5pct_sensitivity.md](top_1pct_top_5pct_sensitivity.md).
- Liquidity and cost detail: see [liquidity_and_cost_sensitivity.md](liquidity_and_cost_sensitivity.md).

## 1. Verdict

Executability at the intended position size is NOT ESTABLISHED.

- Spread: not measured. No bid, ask, order-book or intraday data exists in the repository.
- Intended position size: not defined as a single figure in the sources. Caps and a research notional exist (section 2).
- Entry price: the stored entry equals the signal-day close. The timing of that close relative to the signal is not verified as executable (section 4).
- Volume: daily volume is available for 5,205 of 5,206 rows. At a 1,000 USD notional, 19.2 % of top-1 % rows exceed 5 % of 20-session dollar volume (section 5).
- Gap-through effects on stops and targets are material in the sensitivity (section 6).

## 2. Intended position size: documentation status

| Item | Source | Value | Class |
|---|---|---|---|
| Default equity | `scanner/position_sizer.py` | 10,000 USD | A (code constant) |
| Risk per trade cap | `scanner/position_sizer.py` (`MAX_RISK_PCT`) | 2 % of equity (200 USD) | A (code constant) |
| Minimum risk | `scanner/position_sizer.py` (`MIN_RISK_PCT`) | 0.5 % | A |
| Position cap | `scanner/position_sizer.py` (`MAX_POSITION_PCT`) | 15 % of equity (1,500 USD notional) | A (cap, not a planned size) |
| Portfolio heat cap | `scanner/position_sizer.py` (`PORTFOLIO_HEAT_MAX`) | 6 % | A |
| Kelly fraction | `scanner/position_sizer.py` (`DEFAULT_KELLY_FRAC`) | 0.25 | A |
| Configured position cap | `core/config.py` (`max_position_size`) | 0.2 (20 %) | A, conflicts with the 15 % cap above |
| Research notional | `docs/2026-07-15-p0-execution-replay*.md`, `docs/2026-07-15-v2-precision-execution-research-report.md` | 1,000 USD per signal | B (illustrative research assumption) |
| Product planned notional | none found | not defined | C / UNVERIFIED |

Conclusion: the sources define caps (1,500 USD or 20 % of equity, depending on the file) and a research notional of 1,000 USD. They do not define the position size the product intends to trade. This audit therefore tests two labelled sizes: 1,000 USD (research notional) and 1,500 USD (the 15 % cap in `scanner/position_sizer.py`). Neither is an approved trading size.

## 3. Volume and spread data

| Input | Available | Source | Notes |
|---|---|---|---|
| Daily open, high, low, close | Yes, for 5,206 symbols | `data/price_cache/<SYMBOL>.json` | 529 malformed bar rows were skipped; 195 files include `adjusted_close` |
| Daily volume (shares) | Yes | same | Zero-volume days exist. Dollar volume = close x volume |
| Intraday bars | No | none | Intraday order of high and low cannot be resolved |
| Bid, ask, spread | No | none | Not measured. Status: UNVERIFIED |
| Order book, depth | No | none | Not measured |
| Volume in archive or enriched CSV | No | `signals_archive`, `full_universe_enriched*.csv` | Volume is only in the price cache |

Liquidity measure used: 20-session dollar ADV = mean of (close x volume) over up to 20 sessions up to and including the signal date. One row (0.02 %) has no usable ADV (fewer than 10 sessions of history or zero dollar volume) and is classed as unavailable.

Spread estimators from daily high and low were not applied. They are not validated for sub-1 USD stocks, and no reference spread exists to test them against.

## 4. Entry timing

| Check | Full (n) | Top 1 % (n) | Top 5 % (n) |
|---|---|---|---|
| Entry vs signal-day close, median | -0.021 % (2,907) | +0.007 % (31) | 0.000 % (103) |
| Next session open vs entry, median | +0.048 % (all with a following bar) | +1.962 % | +4.034 % |

Findings:

- For rows with a same-day bar, the stored entry equals the signal-day close.
- 2,299 rows (44.2 %) have a signal date on a Saturday or Sunday. No same-day close exists for them.
- The signal timestamp (`ts`) clusters at 09:00 (2,065 rows) and 21:45 (1,970 rows). Its time zone is not stated in the evidence (UNVERIFIED).
- If the timestamp is after the close, the signal-day close was already past and cannot be bought at the recorded time. If it is before the open, the signal-day close lies in the future and the entry would use information not yet available. Under either reading, the recorded entry is not established as executable.
- The earliest executable price after a signal is the next session open. Next-open prices are above the recorded entry by a median of +1.96 % for the top 1 % and +4.03 % for the top 5 %. The tail winners were gapping up away from the recorded entry.

## 5. Volume feasibility at intended size

Share of signals whose order exceeds the 20-session dollar ADV (pre-specified bands in [liquidity_and_cost_sensitivity.md](liquidity_and_cost_sensitivity.md)):

| Sample | Size | n with ADV | Above 5 % of ADV | Between 1 % and 5 % | Up to 0.1 % |
|---|---|---|---|---|---|
| Full | 1,000 USD | 5,205 | 25 (0.5 %) | 74 | 4,956 |
| Top 1 % | 1,000 USD | 52 | 10 (19.2 %) | 11 | 23 |
| Top 5 % | 1,000 USD | 260 | 17 (6.5 %) | 18 | 185 |
| Full | 1,500 USD | 5,205 | 33 (0.6 %) | 79 | 4,890 |
| Top 1 % | 1,500 USD | 52 | 12 (23.1 %) | 12 | 18 |
| Top 5 % | 1,500 USD | 260 | 22 (8.5 %) | 19 | 172 |

Findings:

- Across the full sample, volume is not a binding constraint at either size.
- In the top tails, the constraint is material. About one in five top-1 % signals would need more than 5 % of its recent dollar volume at 1,000 USD.
- Median dollar ADV: full sample 351.7 M USD; top 1 % 0.30 M USD.
- Volume history covers the signal date for all rows. Whether the cache is complete for thinly traded names is not verified.

## 6. Gap and same-bar effects (sensitivity on 4,631 matched rows)

Matched rows are those where the replay reproduces the stored status (see baseline, section 5). The replay is used only for these sensitivities.

| Sensitivity | Mean on matched rows | Change |
|---|---|---|
| Stored barrier return (baseline) | +0.4441 % (n = 4,631) | none |
| Gap-aware exit (exit at the bar's open when it gaps through the barrier) | -0.0591 % (n = 4,631) | -0.503 pp |
| Stop-first on same-bar take-profit and stop-loss | +0.3235 % (n = 4,631) | -0.121 pp (128 same-bar wins) |
| Next-open entry, valid subset | +0.3510 % (n = 2,540) | not comparable (see below) |

Gap details:

- Wins gapping above target: 662 rows, median exit +5.96 % versus entry.
- Losses gapping through the stop: 1,554 rows, median exit -3.28 % versus entry. Of these, 543 exit below -5 %.
- The gap-aware case assumes a stop-market fill at the open. A limit or stop-limit order may not fill. Both cases are bounded by this audit. Neither is verified.

Next-open entry sensitivity:

- 628 signals had next open at or above target, and 1,463 had next open at or below stop. These cannot be entered at the next open under the barrier rule.
- The valid subset (2,540 rows) is a different population from the full matched sample, so its mean is not comparable and is not used for a conclusion.

Top-tail matched rows:

| Sample | n | Stored | Gap-aware exit | Next-open entry (valid n) |
|---|---|---|---|---|
| Top 1 % | 43 | +20.58 % | +33.02 % | +29.75 % (38) |
| Top 5 % | 237 | +10.72 % | +16.38 % | +11.51 % (163) |

For the top tails the gap-aware case is more favorable, because the winners gap above target. The gap-through losses and the 1,463 entries at or below stop reduce the full-sample result. Both directions are results of the same unverified fill assumptions.

## 7. Adversarial checks

| Check | Result |
|---|---|
| Look-ahead in ADV | ADV uses only sessions up to and including the signal date. Not a look-ahead. |
| Look-ahead in entry | Entry equals the signal-day close. Executability of that close is not established (section 4). |
| Duplicate signals | Not removed. Overlap retained (baseline, section 1). |
| Survivorship | Not verified. The universe history is not reconstructed. |
| Weekend signals | 2,299 rows with no same-day bar. Entry timing for these rows is not verified. |
| Concentration | 48 of 52 top-1 % rows on two dates (sensitivity report, section 6.1). |
| Penny stocks | 17 of 52 top-1 % rows below 1 USD. Spread for these names is not measured. |

## 8. Status of each feasibility element

| Element | Status |
|---|---|
| Intended position size | UNVERIFIED (caps and research notional only) |
| Dollar volume at 1,000 and 1,500 USD | Measured (daily bars, historical) |
| Spread | NOT MEASURED |
| Entry executability | NOT ESTABLISHED |
| Gap-through fill | Sensitivity only, not verified |
| Survivorship and data vintage | UNVERIFIED |
