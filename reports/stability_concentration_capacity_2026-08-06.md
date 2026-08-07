# Stability, Rejection, Concentration and Capacity — 2026-08-06

## Status

Research-only. No scanner, score, portfolio, risk, execution or public
behavior changed. The locked OOS was not opened.

Authority layer: Research. Decision level: Level A for the isolated
measurement infrastructure. Any live No-Trade, sector, capacity or risk rule
would be a Level B/C decision and requires human approval.

## Reproducibility

- Command: `python -m research.stability_concentration_capacity --csv data/backtest_out/full_universe_enriched.csv --cache data/price_cache --out data/backtest_out/stability_concentration_capacity_2026-08-06.json`
- Input: `data/backtest_out/full_universe_enriched.csv`
- Resolved observations: `27,125`
- Target: five-day triple-barrier net return greater than zero
- Barriers: `2.0 * ATR` take-profit, `1.0 * ATR` stop-loss
- Cost assumption: `0.55%` round trip
- Inventory: zero missing paths, 25 short paths, 158 entry-drift rejections
- Temporal split: train through `2026-05-13`, validation through `2026-06-16`, locked OOS through `2026-07-13`

## Stability

| Split | n | Positive net rate | Mean net return | Median net return |
| --- | ---: | ---: | ---: | ---: |
| Train | 8,343 | 36.65% | 0.2605% | -2.0039% |
| Validation | 8,149 | 43.48% | 0.4815% | -1.0500% |

Validation was stronger than train in this sample, but the locked OOS was not
scored. Therefore this is a temporal diagnostic, not evidence of stability or
generalization.

## False rejection

Across all rejected observations:

- rejected: `26,863`
- positive counterfactual outcomes: `11,225`
- false rejection rate: `41.79%`

This is consistent with the earlier baseline and confirms that the current
descriptive veto surface is not yet a reliable rejection-quality system.
Monthly and regime tables are included in the JSON with a minimum group size
gate of 30. Small groups are marked `insufficient_data`.

## Sector concentration

The sector cache covered only `2,254` of `27,125` historical observations,
approximately `8.31%`. The remaining observations are `unknown`. As a result,
the raw sector HHI and top-three share are not decision-grade and must not be
used to infer sector concentration for the full universe.

The runner reports this missingness instead of treating unknown as a real
sector. A future valid sector test needs point-in-time sector membership or a
frozen historical mapping for the whole canonical universe.

## Correlation concentration

The ETF correlation proxy covered `99.99%` of observations and grouped them by
the highest-correlated sector ETF. The largest proxy groups were `XLI`, `XLC`
and `XLF`, together representing approximately `73.64%` of observations.

This is not pairwise candidate correlation. It is a broad market/sector proxy
and cannot establish that selected candidates are independent or that a
portfolio has a particular correlation exposure. Pairwise candidate
correlation remains an open experiment.

## Liquidity capacity

The latest snapshot was evaluated separately on `2026-08-06`:

- usable `dollar_adv` observations: `1,561`
- `liquidity_ok` rate: `11.85%`
- median dollar ADV: `$1,035,871.52`
- median reported position-notional / dollar-ADV ratio: `0.005`
- observed spread-source rate: `0%`

This snapshot was deliberately not joined to historical barrier outcomes, so
it is a current data-quality and capacity diagnostic rather than historical
performance evidence. The zero spread-source observation rate means realistic
spread/impact capacity cannot yet be validated.

## Decision

The next research gate is not promotion of a rule. It is data repair and a
new locked evaluation design:

1. Build point-in-time sector membership for the historical universe.
2. Compute pairwise correlation from overlapping price histories for actual
   candidate sets and portfolio slots.
3. Collect dated spread and impact observations before capacity claims.
4. Obtain explicit human approval before opening the locked OOS.

Artifact: `data/backtest_out/stability_concentration_capacity_2026-08-06.json`
Implementation: `research/stability_concentration_capacity.py`
Tests: `tests/test_stability_concentration_capacity.py`
