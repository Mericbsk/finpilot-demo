# FinPilot Scanner Research End-to-End Completion

Date: 2026-08-11
Layer: Research / Engineering
Level: A - research-only execution and documentation
Status: Completed for feasible diagnostics; confirmatory and production gates remain HOLD/BLOCKED.

## Scope and boundary

This run executed the feasible research sequence against the current canonical
export and price cache. It did not modify the production scanner, score,
ranking, `entry_ok`, TP/SL, exits, portfolio construction, publication,
broker, risk or live behavior. It did not open locked OOS and did not promote
gap, RVOL or ATR hypotheses into product rules.

The research authority is `reports/` as mapped by `docs/INDEX.md`. Product and
risk gaps remain governed by the code/YONERGE boundary; no missing authority
document was invented.

## Ordered execution

### 1. Data identity and cache integrity

Input export:

- `data/backtest_out/full_universe_enriched.csv`
- SHA-256: `e3b183552c7c38755528d133327a0c0601fe0cfff49ba58b9e360d17716ed3d3`
- 48,727 canonical rows; 1,968 symbols in the v2 inventory
- Raw cache: 2,047 symbols

Executed:

```text
python -m research.price_cache_integrity_audit --cache data/price_cache --threshold-pct 50 --field close --out data/backtest_out/price_cache_integrity_audit_2026-08-11_e2e.json
python -m research.price_cache_integrity_audit --cache data/price_cache --threshold-pct 50 --field adjusted_close --out data/backtest_out/price_cache_adjusted_integrity_audit_2026-08-11_e2e.json
```

Results:

- Raw close: 485/2,047 symbols flagged; median largest absolute jump 173.575130%.
- Adjusted close: 148/2,047 symbols flagged; median largest absolute jump 158.787321%.
- Adjusted values exist for 88,440 bars against 907,615 raw close values in the v2 inventory.
- Interpretation: adjustment reduces the flagged set but does not establish corporate-action correctness.

### 2. Label, leakage and protocol controls

The feature-lineage preflight correctly rejects forward field `c2c_5d` as a
feature. The declared temporal split validates. Missing observed commission,
spread, slippage and impact remain `INSUFFICIENT_DATA`; the 55 bps value is a
scenario assumption only.

The focused control suite passed 21/21 tests, including cache integrity,
adjusted-cache behavior, protocol validation, negative controls, decision
quality and v2 controls.

Restatement comparison remains BLOCKED because no immutable prior cache
snapshot exists. The adjusted-cache backfill was not run: it is an external API
write operation that would change the current cache and does not solve the
missing provenance problem without a controlled snapshot protocol.

### 3. Path and cohort validation

Artifact: `data/backtest_out/scanner_battery_v2_2026-08-11.json`.

- Any forward path: 48,727
- Full 5-day path: 43,293
- Full 5-day path with entry drift <=5%: 41,433
- Full 5-day path with entry drift <=1%: 30,088

This cohort separation prevents raw path outliers and missing-horizon rows from
being silently mixed into the headline result.

### 4. Forward diagnostic batteries

The following artifacts were regenerated against the current export/cache and
the fresh integrity audit:

- `data/backtest_out/strategic_lab_current_2026-08-11.json`: 17 COMPLETED, 1 PARTIAL (`X6_invalidation_exit` is a daily proxy, not intraday fill logic).
- `data/backtest_out/ten_perspectives_current_2026-08-11.json`: 13/13 COMPLETED. Two constant-input warnings were recorded by SciPy and do not change the production boundary.
- `data/backtest_out/mirror_analysis_current_2026-08-11.json`: 9/9 COMPLETED.
- `data/backtest_out/negative_controls_current_2026-08-11.json`: 1,000 permutations in each of three null families.
- `data/backtest_out/decision_quality_current_2026-08-11.json`: veto, rejection, loss-taxonomy and model-disagreement diagnostics completed.

Diagnostic hypothesis status:

- Gap conditioning, RVOL conditioning and ATR-parity sizing were measured as exploratory diagnostics only.
- They were not preregistered confirmatory proof and were not promoted to scanner rules.
- No refreshed result validates a stable positive selection edge.

### 5. Portfolio and execution diagnostics

The decision-quality artifact reports 43,093 all rows, 42,788 rejected rows and
305 eligible rows under its 5-day triple-barrier view and 55 bps scenario:

- All: mean net -0.175539%; median -1.860468%; positive rate 39.7466%.
- Rejected: mean net -0.166553%; median -1.830361%; positive rate 39.8149%.
- Eligible: mean net -1.436119%; median -3.397694%; positive rate 30.1639%.

The eligible subset therefore does not beat the descriptive rejected set in
this current run. Flat bps stress remains a scenario, not an observed fill or
capacity model. Intraday ordering, spread, impact, ADV and real broker fills
remain unavailable.

### 6. Null controls and statistical interpretation

The current negative-control candidate has mean net return -1.5663109374% in
the tested candidate sample. Its percentile versus the 1,000-run null families
was 0.0 for label permutation, 0.0 for signal permutation and 0.004 for time
shift. This is not evidence of skill: the candidate is also negative, and the
nulls expose the poor baseline and data/label sensitivity rather than a
positive production edge.

The earlier global multiple-testing controls remain part of the evidence base:
White Reality Check p=0.7413, Hansen SPA p=0.7761 and CPCV/PBO=0.6. These
results do not support selecting a winning configuration from the tested grid.

## Final answers to the requested claims

- Selection / `entry_ok`: not validated. The current eligible cohort is weaker than the descriptive rejected cohort in the decision-quality view.
- Score / ranking: no stable forward monotonicity or independent production edge was established.
- TP/SL and exits: no confirmatory advantage was established; invalidation-exit coverage is partial and intraday ordering is unavailable.
- Portfolio construction: ATR-parity and other sizing views are exploratory; observed capacity and fill data are missing.
- Weekly 5-10% gains: not supported by the available evidence.
- Monthly 10% gains: not a defensible expectation from this dataset; it would require a separate, locked and cost-validating test.
- Gap reversal / RVOL inversion / ATR-parity: HOLD as research hypotheses only.

## Blocked gates

The following remain explicitly blocked and must not be described as validated:

1. Point-in-time listing/delisting universe and survivorship control.
2. Corporate-action classification and provider explanation for flagged jumps.
3. Historical score version/epoch replay.
4. VIX/SPY/sector beta-neutral regime analysis.
5. Observed spread, slippage, impact, ADV-conditioned capacity and fill model.
6. Intraday pullback ordering and execution.
7. Locked OOS and real-user/LLM adversarial evaluation.

## Decision

Research execution is complete for the feasible current-data scope. The
research conclusion is HOLD: preserve the production scanner unchanged, keep
the product position honest as “FinPilot - Daily Market Reasoning,” and do not
claim weekly 5-10% or monthly 10% performance. Any rule change, confirmatory
OOS opening, live release or risk change is outside Level A and requires the
appropriate human approval.

## Evidence and validation

- v2 artifact: `data/backtest_out/scanner_battery_v2_2026-08-11.json`
- Fresh integrity artifacts: `data/backtest_out/price_cache_integrity_audit_2026-08-11_e2e.json`, `data/backtest_out/price_cache_adjusted_integrity_audit_2026-08-11_e2e.json`
- Current diagnostic artifacts listed in Section 4
- Focused control tests: 21/21 passed
- Refreshed battery tests: 25/25 passed
- Production-change marker in v2 artifact: `production_change=false`
