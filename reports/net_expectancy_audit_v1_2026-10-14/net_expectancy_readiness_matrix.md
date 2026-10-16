# Net Expectancy Readiness Matrix (v1)

- Date: 2026-10-14
- Companion files: `net_expectancy_evidence_inventory.md`, `net_expectancy_calculation_spec.md`
- Rule applied: no headline net expectancy is calculated where the readiness gate is not passed.

Status key:

- READY: necessary inputs and methodology exist.
- READY WITH ASSUMPTIONS: a result can be calculated; assumptions must be disclosed with it.
- NOT READY: a critical input or definition is missing.

## 1. Calculation-level readiness

| # | Calculation | Status | Reason | Blocking or disclosed inputs |
|---|---|---|---|---|
| C1 | Gross barrier expectancy, decided rows (reproduces +0.40%) | READY WITH ASSUMPTIONS | Stored labels reproduce exactly (n = 5,206; expectancy +0.3984%). | Assumptions: ideal fill at barrier level; daily bars; take-profit tested before stop-loss on the same bar; no costs; equal weight per signal; overlapping signals retained. |
| C2 | Gross barrier expectancy, first signal per symbol-day | READY WITH ASSUMPTIONS | Deduplication is possible from stored fields. Result: n = 3,802 (decided plus expired), mean +0.303%, median -0.600%. | Same assumptions as C1. Expired rows included. |
| C3 | Gross T+5 close expectancy from `resolved_pct_t5` | NOT READY | Price data contains values from -96% to +11,991% and 166 rows beyond ±50%. A mean of 13.66% is a data artifact. | Price-data audit of the 2025-09 to 2026-09 archive. Clipping at ±50% is not an accepted method. |
| C4 | Outlier sensitivity, top 1% and top 5% by return (barrier labels) | READY | Computed from stored labels. Full-sample result remains primary. Top 1% removed: +0.193%. Top 5% removed: -0.158%. | Disclose that the sign changes at the top 5% cut. |
| C5 | Date-concentration sensitivity (monthly split, date exclusion) | READY | Computed. March 2026 contains 2,501 of 5,206 decided rows (48%), mean +0.662%, median -1.029%. Excluding 2026-03-03 gives mean +0.335%. | Disclose concentration. |
| C6 | Net expectancy with assumed flat cost scenarios (0.20%, 0.55%, 1.00% round-trip) | READY WITH ASSUMPTIONS | The arithmetic is valid: gross minus cost per trade. The cost inputs are assumptions, not measurements. | Sensitivity only. Not an estimate of real trading cost. Sign of result changes between the 0.20% and 0.55% scenarios. |
| C7 | Net expectancy with measured spread and slippage | NOT READY | No bid/ask history. No slippage tracker file. No fills. | Measured spread and fill data, ideally with timestamps and sizes. |
| C8 | Realized broker net expectancy | NOT READY | 11 broker orders, none filled. `trades`, `positions`, `execution_events` are empty. | Filled orders with prices, quantities, fees and timestamps; or broker statements. |
| C9 | Position-sized or portfolio expectancy | NOT READY | No sizing in archive labels. `buy_signals` is empty. No capital model, no concurrency rule. | Documented sizing rule, capital base, and portfolio constraints. |
| C10 | Trade-level variable cost model (spread, volume and size dependent) | NOT READY | No historical spread or dollar-volume series. Capacity flag reports unknown. | Historical bid/ask and dollar-volume data by symbol and date. |
| C11 | Out-of-sample net expectancy | NOT READY | No untouched holdout. The fixed-target holdout state file does not exist, so the holdout is unopened. Earlier documents disagree on the out-of-sample boundary and some periods have been evaluated repeatedly. Opening a holdout requires human approval. | Pre-registered, untouched period with frozen thresholds and a recorded approval. |
| C12 | Paper-trading net expectancy | NOT READY | Paper tables and Redis keys are empty for the current state. | Paper records with fill-equivalent prices and recorded costs. |

## 2. Requirement-level assessment (Phase 5 minimum requirements)

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Clearly defined unit of analysis | READY WITH ASSUMPTIONS | Unit is the archived signal row. Not a unique trade. Overlapping rows exist (5,748 rows on 4,318 symbol-days). |
| 2 | Documented entry convention | READY WITH ASSUMPTIONS | Entry is the stored signal price. Not an executable price. Execution at signal price is assumed. |
| 3 | Documented exit convention | READY WITH ASSUMPTIONS | Take-profit, stop-loss or 21-trading-day close. Same-bar convention is take-profit first, which is optimistic relative to a stop-first convention used in other research. Gap-through behaviour is not modelled. |
| 4 | Defensible return calculation | NOT READY for execution-level claims; READY WITH ASSUMPTIONS for barrier labels | Barrier labels assume ideal fills at barrier levels. Daily bars cannot resolve intraday order. |
| 5 | Defined position-sizing model | NOT READY | No sizing for archive rows. Research notional of 1,000 USD exists only in a separate research run. |
| 6 | Documented cost model | NOT READY | Several conflicting conventions (section 4 of the inventory). None is measured. |
| 7 | Sufficient data to identify overlapping trades | READY | Symbol-day deduplication is possible from stored `symbol` and `ts`. |
| 8 | Reproducible calculation | READY WITH ASSUMPTIONS | Stored-label calculations reproduce. The live database has no frozen snapshot hash. Price inputs are not frozen. |
| 9 | Clear separation of measured and assumed inputs | READY WITH ASSUMPTIONS | Labels are measured from price bars. Costs, sizing and execution conventions are assumed. This audit separates them explicitly. |

## 3. Overall gate result

- Gross barrier expectancy, overlap-adjusted gross expectancy, outlier and date sensitivity: may be reported with the disclosed assumptions.
- Net expectancy per trade with any cost: may only be reported as sensitivity arithmetic, never as an estimate of realized or cost-adjusted performance.
- Realized, position-sized and out-of-sample net expectancy: not calculable from the existing records.
