# High RVOL Raw-OHLC Exit Gate

## Requested gates

The requested validation was: raw OHLC T+1-T+10 returns, ATR-based stops and
maximum adverse excursion, observed costs/spread, matched-control lift and an
independent locked OOS.

## Current status

| Gate | Status | Evidence |
|---|---|---|
| Raw OHLC T+1-T+10 | COMPLETED, integrity warning | `data/price_cache` contains 2,046 populated daily OHLCV files. The raw-bar runner resolved 3,445 High RVOL paths through T+10. The cache audit still flags large price jumps, so raw paths are not yet economically clean. |
| ATR and MAE | COMPLETED, exploratory | Raw bars now provide path highs/lows and a first-touch ATR stop model. The model remains sensitive to cache jumps and does not represent observed fills. |
| Observed cost and spread | BLOCKED | Spread, ADV, slippage, impact, fill ordering and observed execution costs are absent. The 55 bps value remains diagnostic only. |
| Matched control | COMPLETED, exploratory | Existing 100-run same-date control: all `+3.16 pp`, eligible `+0.76 pp`, rejected `+4.15 pp` on the one-day arithmetic mean. |
| Independent locked OOS | NOT OPENED | The data-readiness artifact marks P1/P2 BLOCKED and `locked_oos` NOT_OPENED. Opening it is a Level C human-approval action. |

## Legacy export proxy (for comparison)

The earlier export-only proxy rebuilt the High RVOL cohort with prior-date expanding q90 and the
stored `atr_pct_real`/`mae_t5` fields. Those values are retained only for
comparison; the raw-cache results below supersede them for path analysis.

## Raw-bar ATR/MAE evidence

The High RVOL cohort was rebuilt with prior-date expanding q90 and local raw
OHLC bars. T+1-T+10 close-to-close returns, cumulative MFE/MAE and a first-touch
ATR stop model were calculated for 3,445 complete paths. A putative stop hit
uses the first future low at or below `-k * ATR`; if the next open gaps through
the stop, the model uses the worse of the next open and stop. This is a
conservative model, not observed execution.

| Cohort | Rows | 1 ATR | 1.5 ATR | 2 ATR | MAE median | c2c_5d median |
|---|---:|---:|---:|---:|---:|---:|
| All | 4,163 | 46.1% | 29.1% | 17.6% | -4.57% | +0.07% |
| Eligible | 189 | 61.9% | 46.6% | 32.8% | -6.73% | -2.38% |
| Rejected | 3,974 | 45.4% | 28.2% | 16.9% | -4.50% | +0.12% |

The raw-bar run's selected-path counts were 3,445 all, 233 eligible and 3,212
rejected. The all-cohort one-day matched-control lift was `-8.23 pp`; eligible
was `-27.62 pp`; rejected was `-3.37 pp`. At longer horizons the controls became
economically unstable, with raw jumps producing lifts above `+500 pp` in some
cohorts. Those lifts are data-integrity diagnostics, not signal evidence.

The raw close-return medians were near zero for all/rejected at most horizons,
while the 0.55% cost-adjusted clipped means stayed near zero or negative. The
eligible cohort was negative through day 8 and had only 233 complete paths.

Representative raw-bar stop results:

| Cohort | Horizon | 1 ATR hit | 1.5 ATR hit | 2 ATR hit | 1.5 ATR clipped net |
|---|---:|---:|---:|---:|---:|
| All | 5d | 49.0% | 32.0% | 20.1% | -0.55% |
| Eligible | 5d | 66.1% | 49.4% | 36.9% | -1.68% |
| Rejected | 5d | 47.8% | 30.7% | 18.9% | -0.47% |
| All | 10d | 59.9% | 44.5% | 31.6% | -0.88% |
| Eligible | 10d | 72.5% | 62.2% | 48.9% | -0.35% |
| Rejected | 10d | 59.0% | 43.2% | 30.4% | -0.92% |

## Decision

No fixed exit point is validated. In particular, these results do not support
“exit on day 5”, “exit on day 8” or a production ATR stop. The eligible cohort
has negative five-day median return and the stop proxy has no path or execution
semantics.

The next executable step requires a corrected immutable raw-bar snapshot keyed
by `symbol`, `scan_date`, `open`, `high`, `low`, `close`, adjusted corporate
action lineage and volume, plus observed spread/slippage or a documented
execution model. The current cache technically supplies OHLC, but its jump
audit is not clean: adjusted-close audits still flag 148 symbols with large
jumps. An independent locked OOS must remain closed until the P1/P2 gates pass
and human approval is recorded.

Production, paper/live and scanner/exit behavior were not changed.
