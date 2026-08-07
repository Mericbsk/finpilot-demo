# Entry Quality Research Experiment

Date: 2026-08-06
Status: research-only, no production rule change
Decision level: Level B if a result is later proposed for the live entry gate

## Question

Does a stricter entry-quality profile produce better outcomes than the current
`entry_ok` gate? The live gate was not changed. The experiment re-labels the
existing historical artifact with alternative research predicates.

## Input and method

Input artifact:

- `data/backtest_out/full_universe_enriched.csv`
- 53,859 raw rows
- scan dates: 2025-09-11 through 2026-07-13
- 1,932 symbols in the cached price universe
- canonical policy: earliest row per `(symbol, scan_date)`
- canonical rows before path resolution: 27,386
- 27,125 canonical rows resolved for the 5-day path
- 581 rows rejected for entry drift and 50 rows had short paths

Execution-style outcome:

- forward horizon: 5 trading days
- take-profit: 2.0 x ATR
- stop-loss: 1.0 x ATR
- stop-first same-bar handling from `scanner.labeling.triple_barrier_label`
- research round-trip cost: 0.55 percentage points
- `cost_adjusted_expectancy_pct = gross expectancy - 0.55`

The experiment used a corrected local research harness because the existing
barrier runner does not retain `score` in its internal row model and stores
`regime` as text. No production module was modified.

## Profiles

- `entry_ok`: current historical gate label.
- `score_3`: raw score exactly 3, without requiring the stored `entry_ok` label.
- `score_2`: raw score exactly 2; research candidate only, not a production rule.
- `score_ge_2_regime_direction`: raw score at least 2 plus regime and direction.
- `entry_ok_rvol_ge_2`: baseline plus RVOL at least 2.
- `entry_ok_atr_ge_6`: baseline plus ATR percentage at least 6.

The artifact does not contain `alignment_ratio`, `momentum_ratio`,
`filter_score`, RSI, MACD, or the volume sub-components. Therefore the
alignment and momentum-confluence profiles requested for the next experiment
could not be evaluated on this artifact without inventing values. This is a
telemetry/data-lineage gap, not a negative result.

## Canonical 5-day barrier results

| Profile | N | TP | SL | Time | Gross expectancy % | Cost-adjusted expectancy % | Median return % | PF | Max return loss % | Worst MAE % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `entry_ok` | 799 | 25.91% | 53.19% | 20.90% | 0.107 | -0.443 | -2.144 | 1.042 | -32.997 | -41.409 |
| `score_3` | 951 | 25.34% | 58.99% | 15.67% | -0.085 | -0.635 | -1.890 | 0.971 | -37.989 | -78.740 |
| `score_2` | 7,465 | 27.06% | 50.19% | 22.75% | 1.351 | 0.801 | -0.989 | 1.577 | -54.885 | -92.551 |
| `score_ge_2_regime_direction` | 3,320 | 29.16% | 51.27% | 19.58% | 0.489 | -0.061 | -0.730 | 1.228 | -46.109 | -92.551 |

These results are descriptive research evidence only. They are not a
production performance claim and do not prove that score 2 is better. The
score-2 cohort is much larger, has different selection exposure, and shows
larger worst-case losses.

## Forward movement check

The artifact's `resolved_pct_t5` is a favorable-movement field, not a realized
net return. It must not be presented as execution P&L.

| Profile | N | Hit `resolved_pct_t5 >= 5%` | Mean favorable movement % | Median favorable movement % |
|---|---:|---:|---:|---:|
| `entry_ok` | 799 | 41.68% | 7.159 | 4.142 |
| `score_3` | 951 | 40.48% | 14.074 | 3.624 |
| `score_2` | 7,465 | 37.91% | 11.358 | 3.368 |
| `score_ge_2_regime_direction` | 3,320 | 35.78% | 5.870 | 3.176 |

The divergence between favorable movement and barrier outcomes is expected:
movement capture does not establish stop-before-target ordering, execution
cost, or realized P&L.

## Stability observations

- `entry_ok` canonical barrier expectancy was positive in April (3.685%) but
  negative in May (-0.835%) and June (-0.351%).
- `score_3` was positive in April (0.757%) and June (0.456%), but negative in
  May (-0.705%) and July (-1.292%).
- `score_2` was strongly positive in April (13.486%), approximately flat in May
  (-0.003%), positive in June (1.137%), and negative in July (-1.412%).
- The April result is a concentration warning, not evidence of stable edge.
- Worst MAE values indicate material outlier and corporate-action/price-scale
  sensitivity that needs separate data-quality controls.

## Interpretation

1. A binary `score == 3` gate is not demonstrated to be a reliable quality
   ordering. In this artifact it is not consistently better than `score == 2`
   across outcome definitions or months.
2. Adding a new total score now would amplify the known overlap between raw
   RSI/volume/MACD checks, filter score, trend, alignment, and momentum.
3. The first experiment supports separating three concepts:
   - eligibility gate: current production `entry_ok`;
   - quality measurement: research profile labels and continuous telemetry;
   - ordering: ranking among eligible rows.
4. No live rule should be changed from this result. A score-2 alignment profile
   remains a Level B product/quant proposal and must be tested with the missing
   point-in-time fields.

## Next experiment gate

Before testing alignment/confluence as quality dimensions, the scanner export
or replay artifact must retain, at minimum:

- raw score and its three components: RSI, volume, MACD;
- `filter_score` and its three components: volume spike, price momentum,
  trend strength;
- `alignment_ratio` and `timeframe_aligned`;
- `momentum_ratio` and `momentum_confluence`;
- feature timestamp/age and canonical symbol-day identity;
- triple-barrier labels and cost model version.

The next comparison should be pre-registered with the existing research
protocol, use discovery/validation/locked-OOS time splits, and report signal
count, T+5 movement separately, cost-adjusted triple-barrier expectancy,
median return, TP/SL/time rates, PF, maximum loss, MAE, and regime/month
breakdowns. Until those fields exist, alignment/confluence conclusions are
`insufficient_data`.
