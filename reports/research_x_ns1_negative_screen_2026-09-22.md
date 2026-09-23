# RESEARCH-X/NS-1 - Negative-Screen Battery Result

**Date:** 2026-09-22
**Level:** A - read-only forensic research
**Preregistration:** reports/research_x_ns1_negative_screen_preregistration_2026-09-22.md (APPROVED/LOCKED)
**Input SHA-256 ok:** True | n=34762 | dates=54 | input_mismatch=False

**Overall:** NO_SCREEN_SUPPORTED

## Primary verdicts (metric: median kept - median removed, ANS-1 contract)

| Rule | Verdict | Kept median | Removed median | Improvement (pp) | Adj CI 98.75% | Big-loser not increased | Early pp | Late pp | Same sign | Loser recall |
|---|---|---|---|---|---|---|---|---|---|---|
| NS-A | SCREEN_NOT_SUPPORTED | 0.299263 | -2.325581 | 2.624845 | [-0.24398, 4.566254] | True | 1.020495 | 4.196745 | True | 0.799679 |
| NS-B3 | SCREEN_PARTIAL | 0.0 | -3.471634 | 3.471634 | [1.843462, 5.463744] | True | 3.107104 | 4.240948 | True | 0.302892 |
| NS-C | SCREEN_PARTIAL | 0.04006 | -3.144856 | 3.184916 | [1.857418, 7.539265] | True | 1.201245 | 3.56823 | True | 0.337172 |
| NS-UNION | SCREEN_NOT_SUPPORTED | 0.299188 | -2.325581 | 2.62477 | [-0.491817, 4.36194] | True | 1.020495 | 4.137637 | True | 0.80075 |

## Secondary / descriptive arms (no verdict)

| Arm | Removed n | Observed median improvement (pp) | Big-loser kept | Loser recall |
|---|---|---|---|---|
| NS-B4 | 1438 | 4.528368 | 0.097797 | 0.127209 |
| B3-atr | 6978 | 3.536594 | 0.061762 | 0.540439 |
| B3-lottery | 4854 | 3.184916 | 0.082754 | 0.337172 |
| B3-price | 6986 | 2.100196 | 0.082013 | 0.38993 |
| B3-dist | 6978 | 2.025514 | 0.081702 | 0.392073 |
| PRICE5 | 26689 | -2.099865 | 0.202775 | 0.561596 |

## Interpretation (post-hoc, clearly separated from verdicts)

**Replication check (NS-A):** point estimate matches ANS-1 exactly
(median kept-removed = 2.624845pp; kept 0.299 / removed -2.326;
big-loser 22.2% -> 3.5%; loser recall 80.0%; removed n=13,433).
The ANS-1 lock and its SUPPORTED verdict are NOT reopened or weakened.

**Why NS-A reads SCREEN_NOT_SUPPORTED here despite matching ANS-1:**
the two studies ask different statistical questions. ANS-1 places the CI
around the kept-vs-removed median difference (95% CI [0.16, 3.86],
excludes 0). NS-1's locked question is whether REMOVING the flagged rows
improves the remaining universe; under the wider percentile bootstrap of
that quantity plus family-wise Bonferroni (98.75%), the adjusted CI
[-0.24, 4.57] contains zero. Same point estimate, wider interval,
different estimand - not a contradiction, and NOT an invalidation of ANS-1.

**NS-B3 (failure-profile majority rule):** SCREEN_PARTIAL - the adjusted
CI excludes zero, matched-random and null-shuffle pass, big-loser rate
falls (10.7% -> 8.5%), but the effect is not significant in BOTH temporal
halves (early significant, late not). This matches the ANS-3 lesson that a
screening effect seen in one period is not sufficient by itself.

**NS-C (lottery only):** SCREEN_PARTIAL - same pattern as NS-B3.

**NS-UNION:** tracks NS-A almost exactly (removed n=13,470 vs 13,433);
NS-B3 adds only ~37 rows to the NS-A flag, so the union inherits NS-A's
verdict. NS-B3's signal is largely a subset of the ANS-1 attention flag.

**PRICE5 (robustness arm):** NEGATIVE improvement (-2.10pp) - removing
sub-$5 rows REMOVES big winners faster than losers and WORSENS the kept
universe. This is a valid, pre-declared descriptive finding: a naive
low-price exclusion is harmful, and it warns against treating the
price<=p20 leg of NS-B3 as a standalone rule.

**Missing-field note:** NS-B3/NS-C/NS-UNION could not evaluate 10,580
rows (missing lottery_factor/price/dist_52w_high on those dates); those
rows conservatively stayed in the universe (cannot be eliminated).

## Governance

Screening evidence is NOT a buy signal and NOT a production filter.
No score, ranking, scanner, configuration, scheduler, database, publication,
or user-facing surface was changed. H2/H4 chain remains CLOSED/FROZEN.
ANS-1/ANS-2/ANS-3 verdicts unchanged. production_impact = NONE.
