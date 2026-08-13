# Research Data Readiness Audit

Date: 2026-08-11
Layer: Research / Engineering
Level: A - research-only audit
Production change: none

## Current evidence

The repository was audited with `research/data_readiness_audit.py` and the
machine-readable result was written to
`data/backtest_out/data_readiness_audit_2026-08-11.json`.

| Input | Observed | Gate meaning |
|---|---:|---|
| Daily price-cache files | 2,047 files / 96,322,622 bytes | Current data exists; it is not an immutable prior snapshot |
| Intraday cache | 880 files / 129,947 bars | Intraday bars exist, but they are not execution observations |
| PIT universe | `symbol` only | Listing/delisting dates and ticker lineage are absent |
| Execution records | 0 complete records | No same-record spread, slippage, impact and fill-price observation |

## Gate result

- P1 data reliability: `BLOCKED`
- P2 label and execution: `BLOCKED`
- H1 gap-reversal, H2 RVOL-inversion and H3 ATR-parity: `HOLD`
- Locked OOS: `NOT_OPENED`

The intraday cache is now explicitly recognized as available bar data. It does
not open P2 because the declared execution contract requires observed spread,
slippage, impact, fill price and capacity context. The existing ADV helper
caches do not satisfy that contract.

## Ordered next work

1. Acquire and version a PIT security master with listing/delisting dates,
   ticker lineage and delisting returns.
2. Acquire corporate-action/provider provenance and classify the flagged price
   jumps against adjusted and raw bars.
3. Preserve a complete bar-cache snapshot, not only a hash manifest, then run
   the restatement detector against a later snapshot.
4. Join intraday bars to observed fills or a documented execution feed carrying
   spread, slippage, impact, fill price, ADV and timestamp.
5. Re-evaluate P1 and P2. Only if both pass, run the pre-registered H1/H2/H3
   confirmatory designs on independent data or the reserved holdout.
6. Keep locked OOS closed until the prerequisite phases pass and human approval
   is recorded.

The hash manifest at
`data/backtest_out/price_cache_snapshot_manifest_2026-08-11.json` records
current-file provenance only; `restatement_comparison_ready` remains false.
No production scanner, score, ranking, entry/exit, portfolio, publication,
broker, risk or live behavior changed.
