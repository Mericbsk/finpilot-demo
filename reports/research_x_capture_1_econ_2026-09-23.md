# RESEARCH-X/RX-CAPTURE-1-ECON - Economic & Robustness Review Result

**Date:** 2026-09-23
**Level:** B (read-only economic/robustness review)
**Overall:** FURTHER_VALIDATION_SUPPORTED

| Candidate | Verdict | Breakeven cost | Median net @1.00 | Temporal sign consistent | Conc warn |
|---|---|---|---|---|---|---|
| E1_t3 | FURTHER_VALIDATION_SUPPORTED | BETWEEN_GRID_POINTS | 2.0 | True | False |
| E1_t5 | INCONCLUSIVE | 1.75 | 0.68587 | False | False |

## Interpretation (post-hoc, separated from verdicts)

**Median-vs-mean divergence (both candidates):** the primary median is
positive but the MEAN net capture is NEGATIVE (E1_t3 mean -0.832pp,
E1_t5 mean -0.841pp at 0.55% cost). This confirms the locked median
degenerates to the fixed target (majority hit +3%/+5% on first touch)
while the tail is heavy-negative. The median estimand answers the
locked question; the mean carries the tail-risk information and is
reported here as secondary. A positive median with a negative mean is
a concentration/skew signal, not a contradiction.

**E1_t3 (FURTHER_VALIDATION_SUPPORTED):** breakeven is
BETWEEN_GRID_POINTS (median never crosses zero on the grid: +3.0 @0%,
+2.0 @1.00%, +1.0 @2.00%); survives the 1.00 stress gate; temporal sign
consistent (early=late at both cost levels); no concentration warning.
NOTE: this is the median-degenerate candidate (hit share ~61.5%); its
positive median reflects 'most rows hit +3% quickly', not a
discriminating return distribution.

**E1_t5 (INCONCLUSIVE):** breakeven = 1.75 (median crosses zero between
1.50 and 2.00); survives 1.00 gate; BUT temporal sign consistency FAILS
at the 1.00 stress level (early +1.106 vs late -0.333) - the late-period
weakening noted in RX-CAPTURE-1 (1.556 -> 0.117 at 0.55%) becomes a sign
reversal under stress. Per the locked engine, a primary-positive but
temporally-inconsistent result is INCONCLUSIVE, not NOT_SUPPORTED
(UNKNOWN != NOT_SUPPORTED is preserved).

**Economic boundary:** spread/slippage observation = 0% (real execution
cost unknown); liquidity proxy = NOT_MEASURABLE; new-data temporal
replication = NOT_AVAILABLE. These are recorded limitations, not
failures. This review does NOT validate real-world executability.

## Governance

FURTHER_VALIDATION_SUPPORTED != production approval. This review only answers
'is the CAPTURE_SUPPORTED finding worth carrying into more realistic testing?'.
Assumed cost sensitivity != observed transaction cost; breakeven estimate != realized execution cost.
Liquidity = NOT_MEASURABLE (proxy only); new-data temporal replication = NOT_AVAILABLE.
production_impact = NONE. H4 FROZEN. RX-CAPTURE-1 unchanged.
