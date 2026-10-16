# Net Expectancy Calculation Specification (v1)

- Date: 2026-10-14
- Companion files: `net_expectancy_evidence_inventory.md`, `net_expectancy_readiness_matrix.md`
- Scope: calculations marked READY or READY WITH ASSUMPTIONS in the readiness matrix. Calculations marked NOT READY are specified only by their blocking inputs.
- Status: specification for reproduction. Not a strategy definition. Not an investor figure.

## 1. Data access (read-only)

- Source: table `signals_archive` in `data/finpilot.db`.
- Connection: `sqlite3.connect(<path as file URI>?mode=ro, uri=True)` followed by `PRAGMA query_only=ON`.
- Do not initialize the application `Database()` class, which creates directories and schema.
- Freeze requirement before any future publication of these numbers: record SHA-256 of a copy of the database taken while no service writes to it.

## 2. Inclusion rules

- Decided population (karne-consistent): `resolved_status_barrier IN ('resolved_win', 'resolved_loss')` and `resolved_pct_barrier IS NOT NULL`.
- Extended population: decided population plus `expired_win` and `expired_loss`.
- Excluded: `resolved_status_barrier IS NULL` (532 rows at capture).

## 3. Gross barrier expectancy (C1, READY WITH ASSUMPTIONS)

Let `r_i` be `resolved_pct_barrier` for row `i` (percent of entry price), `W` the set of wins and `L` the set of losses within the decided population.

- Hit rate: `p = |W| / (|W| + |L|)`
- Mean win: `w_bar = mean(r_i for i in W)`
- Mean loss: `l_bar = mean(r_i for i in L)`
- Gross expectancy: `E_gross = p * w_bar + (1 - p) * l_bar`
- Identity check: `E_gross = mean(r_i for all i in decided population)`. Both forms must agree.
- Asymmetry ratio: `A = w_bar / |l_bar|`

Reproduction values at capture (decided population): `n = 5,206`, `|W| = 1,565`, `|L| = 3,641`, `p = 0.3006`, `w_bar = +4.2825`, `l_bar = -1.2711`, `E_gross = +0.3984`, `A = 3.369`.

Assumptions carried with the result:

- Entry at stored signal price.
- Exit at barrier level, with no gap-through adjustment.
- Take-profit test precedes stop-loss test on the same daily bar.
- Daily bars only.
- Zero costs.
- Each row weighted equally.

## 4. Overlap-adjusted gross expectancy (C2, READY WITH ASSUMPTIONS)

- Sort extended population by `(ts, id)` ascending.
- Keep the first row for each `(symbol, date(ts))`.
- Apply section 3 to the kept rows.

Capture values: `n = 3,802`, `E_gross_mean = +0.3029`, median `-0.6003`, hit rate `0.2788`.

## 5. Median and distribution (required alongside mean)

- Report median and hit rate with every expectancy.
- If median is negative while mean is positive, the mean must not be presented alone. The result is then described as dependent on a minority of large winners.

Capture values (decided population): median `-0.6431`.

## 6. Outlier sensitivity (C4, READY)

- Full-sample result is primary.
- Sensitivity A: remove rows whose `r_i` is in the top 1% by value (over the extended population), then apply section 3.
- Sensitivity B: remove the top 5% by value, then apply section 3.
- Report the removed count, remaining count and resulting mean.

Capture values: top 1% removed, `n = 5,164`, mean `+0.1931`. Top 5% removed, `n = 4,956`, mean `-0.1582`.

## 7. Date-concentration sensitivity (C5, READY)

- Group decided rows by calendar month of `ts`.
- Report count, share of total, mean and median per month.
- Exclude the single date with the largest number of extreme T+5 values (2026-03-03) as a sensitivity only.

Capture values: March 2026 `n = 2,501` (48% of decided rows), mean `+0.6620`, median `-1.0293`. Date 2026-03-03 `n = 473`, mean `+1.0319`, median `-1.4683`. Excluding that date, `n = 4,733`, mean `+0.3351`.

## 8. Flat cost scenario arithmetic (C6, READY WITH ASSUMPTIONS, sensitivity only)

For each scenario with round-trip cost `c` (percent of entry):

- Per-trade net return: `r_i^net = r_i - c`
- Net expectancy: `E_net(c) = E_gross - c` (valid because the cost is flat and applied to every row)

Scenarios and their provenance:

| Scenario | `c` (round-trip, %) | Provenance | Status |
|---|---|---|---|
| S1 | 0.20 | `scanner/evaluate.py` flat cost constant; equals research v2 convention of 5 bps per side slippage plus 5 bps per side commission | Assumed |
| S2 | 0.55 | Research baseline | Assumed |
| S3 | 1.00 | Research stress | Assumed |

Sensitivity arithmetic at capture (`E_gross = +0.3984`):

- S1: approximately +0.20
- S2: approximately -0.15
- S3: approximately -0.60

Interpretation rule: these numbers show that the sign of the result depends on the assumed cost. They are not an estimate of trading cost and must not be presented as expectancy after costs.

Spread and slippage are not separately subtracted. Doing so would double-count if a scenario already includes them, and no measured spread exists to justify any separate term.

## 9. Calculations that are not ready (blocking inputs only)

- C3 (T+5): requires an adjusted-price audit of `resolved_pct_t5` source data, including explanation of values beyond ±50%.
- C7 (measured-cost net): requires historical bid/ask and fill records with timestamps, sizes and fees.
- C8 (realized net): requires filled broker orders with prices, quantities, fees and timestamps.
- C9 (sized or portfolio): requires a documented sizing rule, capital base and concurrency constraints.
- C10 (variable cost model): requires historical dollar-volume and spread series by symbol and date.
- C11 (out-of-sample net): requires a pre-registered, untouched period, frozen thresholds and recorded human approval. The fixed-target holdout state file is absent, so the holdout is unopened.
- C12 (paper net): requires paper records with recorded fill-equivalent prices and costs.

## 10. Validation requirements for any future version

- Reproduce section 3 from a frozen database copy and record its SHA-256.
- Report counts for every population used, including excluded rows and reasons.
- Report mean, median, hit rate and asymmetry together.
- Keep full-sample results as the primary descriptive figures; sensitivities are secondary.
- Do not change the inclusion rules or cost scenarios after seeing results.
- Any net figure must name its cost source, its scenario and its population.

## 11. Known defects to fix before a v2 specification

- Same-bar convention is take-profit first. A stop-first sensitivity is required.
- Stop-loss exits are recorded at the stop level even when the daily open is below it. A gap-aware sensitivity is required.
- `auto_adjust=True` applied to bars combined with unadjusted signal-time entry prices. Corporate-action mismatch test is required.
- Overlapping signals are counted separately in karne. Deduplicated figures must accompany the raw figure.
- `paper_portfolio.py` comment and code disagree on round-trip cost. The code value is 20 bps; the comment says 10 bps.
